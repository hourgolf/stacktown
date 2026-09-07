// Ported from Content/Python/citytick.py. See StacktownEconomy.h for the split
// between this file and the pure rules layer, and for why this subsystem
// refuses to write anything until it is told where.

#include "StacktownEconomy.h"

#include "StacktownAlpha.h"
#include "Dom/JsonObject.h"
#include "Dom/JsonValue.h"
#include "StacktownPlacement.h"
#include "StacktownWorldBoard.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "HAL/PlatformProcess.h"
#include "HAL/FileManager.h"
#include "Serialization/JsonReader.h"
#include "Serialization/JsonSerializer.h"
#include "Serialization/JsonWriter.h"
#include "Policies/CondensedJsonPrintPolicy.h"

namespace Stacktown
{

static bool ParseJsonObject(const FString& JsonText, TSharedPtr<FJsonObject>& Out, FString& OutError)
{
	const TSharedRef<TJsonReader<TCHAR>> Reader = TJsonReaderFactory<TCHAR>::Create(JsonText);
	if (!FJsonSerializer::Deserialize(Reader, Out) || !Out.IsValid())
	{
		OutError = FString::Printf(TEXT("malformed JSON: %s"), *Reader->GetErrorMessage());
		return false;
	}
	return true;
}

static FString WriteJsonObject(const TSharedRef<FJsonObject>& Object)
{
	FString Out;
	const TSharedRef<TJsonWriter<TCHAR, TCondensedJsonPrintPolicy<TCHAR>>> Writer =
		TJsonWriterFactory<TCHAR, TCondensedJsonPrintPolicy<TCHAR>>::Create(&Out);
	FJsonSerializer::Serialize(Object, Writer);
	return Out;
}

/** Required-key read. A ruleset with a missing or non-numeric key is a broken
 *  ruleset and must say so, not quietly inherit a default and run as if it were
 *  the owner's tuning. */
static bool ReadNumber(const TSharedPtr<FJsonObject>& Obj, const TCHAR* Key, double& Out, FString& OutError)
{
	if (!Obj->TryGetNumberField(Key, Out))
	{
		OutError = FString::Printf(TEXT("econrules.json: missing or non-numeric key '%s'"), Key);
		return false;
	}
	return true;
}

bool FEconRules::FromJson(const FString& JsonText, FEconRules& Out, FString& OutError)
{
	TSharedPtr<FJsonObject> Root;
	if (!ParseJsonObject(JsonText, Root, OutError))
	{
		return false;
	}

	FEconRules R;
	double CreditsPerN = 0.0;
	const bool bAll =
		ReadNumber(Root, TEXT("money_start"),           R.MoneyStart,        OutError) &&
		ReadNumber(Root, TEXT("price_base"),            R.PriceBase,         OutError) &&
		ReadNumber(Root, TEXT("price_per_100uu"),       R.PricePer100uu,     OutError) &&
		ReadNumber(Root, TEXT("price_per_tier"),        R.PricePerTier,      OutError) &&
		ReadNumber(Root, TEXT("rent_per_tier"),         R.RentPerTier,       OutError) &&
		ReadNumber(Root, TEXT("growth_threshold"),      R.GrowthThreshold,   OutError) &&
		ReadNumber(Root, TEXT("demand_default"),        R.DemandDefault,     OutError) &&
		ReadNumber(Root, TEXT("trade_credits_per_n"),   CreditsPerN,         OutError) &&
		ReadNumber(Root, TEXT("trade_credit_amount"),   R.TradeCreditAmount, OutError) &&
		ReadNumber(Root, TEXT("trade_bonus_per_win"),   R.TradeBonusPerWin,  OutError) &&
		ReadNumber(Root, TEXT("demand_gain"),           R.DemandGain,        OutError) &&
		ReadNumber(Root, TEXT("demand_loss"),           R.DemandLoss,        OutError) &&
		ReadNumber(Root, TEXT("demand_rate"),           R.DemandRate,        OutError) &&
		ReadNumber(Root, TEXT("demand_min"),            R.DemandMin,         OutError) &&
		ReadNumber(Root, TEXT("demand_max"),            R.DemandMax,         OutError) &&
		ReadNumber(Root, TEXT("wear_ticks_per_tier"),   R.WearTicksPerTier,  OutError) &&
		ReadNumber(Root, TEXT("road_highway_reach"),    R.RoadHighwayReach,  OutError);
	if (!bAll)
	{
		return false;
	}
	// recipe_mult (optional, 2026-09-06 night): {"office": {"price": 1.6, "rent": 1.5}, ...}
	const TSharedPtr<FJsonObject>* Mults = nullptr;
	if (Root->TryGetObjectField(TEXT("recipe_mult"), Mults) && Mults && Mults->IsValid())
	{
		// The three recipes the catalogue knows (5.8's FJsonObject keys are shared
		// strings, not FStrings; asking by name sidesteps the conversion). A recipe
		// absent here is vernacular, 1.0 / 1.0.
		static const TCHAR* Recipes[] = { TEXT("vernacular"), TEXT("office"), TEXT("tower") };
		for (const TCHAR* Rid : Recipes)
		{
			const TSharedPtr<FJsonObject>* One = nullptr;
			if ((*Mults)->TryGetObjectField(Rid, One) && One && One->IsValid())
			{
				FRecipeMult M;
				(*One)->TryGetNumberField(TEXT("price"), M.Price);
				(*One)->TryGetNumberField(TEXT("rent"), M.Rent);
				R.RecipeMult.Add(FString(Rid), M);
			}
		}
	}

	// ROAD TYPES. Four families x four types, read by building the key from the
	// type name rather than listing sixteen literals - the names come from
	// RoadTypeNames(), the single place the four are enumerated, so adding a
	// fifth type is a rules-file edit plus one entry there, not sixteen.
	// REQUIRED like every other key: a ruleset missing a type's cost is broken,
	// and inheriting the compiled default would run a typo as if it were tuning.
	R.RoadTypes.Reset();
	for (const FString& Type : RoadTypeNames())
	{
		FRoadTypeRules T;
		double Frontage = 0.0;
		const bool bType =
			ReadNumber(Root, *FString::Printf(TEXT("road_cost_per_100uu_%s"), *Type), T.CostPer100uu, OutError) &&
			ReadNumber(Root, *FString::Printf(TEXT("road_rent_mult_%s"),      *Type), T.RentMult,     OutError) &&
			ReadNumber(Root, *FString::Printf(TEXT("road_width_%s"),          *Type), T.Width,        OutError) &&
			ReadNumber(Root, *FString::Printf(TEXT("road_frontage_%s"),       *Type), Frontage,       OutError);
		if (!bType)
		{
			return false;
		}
		// The JSON carries 1/0 rather than true/false so the owner edits the
		// same kind of number in every row of the table.
		T.bFrontage = Frontage != 0.0;
		R.RoadTypes.Add(Type, T);
	}

	if (CreditsPerN < 1.0)
	{
		// Milestone arithmetic divides by this. The Python would raise; refusing
		// the ruleset outright is the same answer said earlier.
		OutError = FString::Printf(TEXT("econrules.json: trade_credits_per_n must be >= 1, got %g"), CreditsPerN);
		return false;
	}
	R.TradeCreditsPerN = static_cast<int32>(CreditsPerN);

	Out = R;
	return true;
}

bool CityStateFromJson(const FString& JsonText, FCityState& Out, FString& OutError)
{
	TSharedPtr<FJsonObject> Root;
	if (!ParseJsonObject(JsonText, Root, OutError))
	{
		return false;
	}

	FCityState S;
	if (!Root->TryGetNumberField(TEXT("money"), S.Money))
	{
		OutError = TEXT("citystate: missing or non-numeric 'money'");
		return false;
	}
	if (!Root->TryGetNumberField(TEXT("demand"), S.Demand))
	{
		OutError = TEXT("citystate: missing or non-numeric 'demand'");
		return false;
	}

	// Absent in every save written before the trade ledger existed. Zero is the
	// correct reading of "no trades counted yet", so this is a default rather
	// than a migration.
	int32 Processed = 0;
	Root->TryGetNumberField(TEXT("trades_processed"), Processed);
	double Goals = 0.0;
	Root->TryGetNumberField(TEXT("goals_reached"), Goals);   // optional: absent on every save before 2026-09-06 night
	S.GoalsReached = (int32)Goals;
	S.TradesProcessed = Processed;

	const TSharedPtr<FJsonObject>* Roads = nullptr;
	if (Root->TryGetObjectField(TEXT("roads"), Roads) && Roads != nullptr && Roads->IsValid())
	{
		for (const TPair<FString, TSharedPtr<FJsonValue>>& Pair : (*Roads)->Values)
		{
			const TSharedPtr<FJsonObject>* RObj = nullptr;
			if (!Pair.Value.IsValid() || !Pair.Value->TryGetObject(RObj) || RObj == nullptr)
			{
				OutError = FString::Printf(TEXT("citystate: road '%s' is not an object"), *Pair.Key);
				return false;
			}
			FRoadSegment Seg;
			const TArray<TSharedPtr<FJsonValue>>* Start = nullptr;
			const TArray<TSharedPtr<FJsonValue>>* End = nullptr;
			// start/end are two-element arrays in the Python's own shape.
			if (!(*RObj)->TryGetArrayField(TEXT("start"), Start) || Start->Num() != 2
				|| !(*RObj)->TryGetArrayField(TEXT("end"), End) || End->Num() != 2)
			{
				OutError = FString::Printf(
					TEXT("citystate: road '%s' needs two-element start and end"), *Pair.Key);
				return false;
			}
			Seg.StartX = (*Start)[0]->AsNumber();
			Seg.StartY = (*Start)[1]->AsNumber();
			Seg.EndX   = (*End)[0]->AsNumber();
			Seg.EndY   = (*End)[1]->AsNumber();
			(*RObj)->TryGetStringField(TEXT("width_class"), Seg.WidthClass);
			// 'path' groups the chords of one curve (item 11). Optional, and
			// absent means the segment is its own road - which is what every
			// straight draw and everything written before curves is.
			(*RObj)->TryGetStringField(TEXT("path"), Seg.Path);
			S.Roads.Add(Pair.Key, Seg);
		}
	}

	const TSharedPtr<FJsonObject>* Parcels = nullptr;
	if (Root->TryGetObjectField(TEXT("parcels"), Parcels) && Parcels != nullptr && Parcels->IsValid())
	{
		for (const TPair<FString, TSharedPtr<FJsonValue>>& Pair : (*Parcels)->Values)
		{
			const TSharedPtr<FJsonObject>* PObj = nullptr;
			if (!Pair.Value.IsValid() || !Pair.Value->TryGetObject(PObj) || PObj == nullptr)
			{
				OutError = FString::Printf(TEXT("citystate: parcel '%s' is not an object"), *Pair.Key);
				return false;
			}
			FParcelState P;
			(*PObj)->TryGetStringField(TEXT("rid"), P.Rid);
			(*PObj)->TryGetNumberField(TEXT("tier"), P.Tier);
			(*PObj)->TryGetNumberField(TEXT("width"), P.Width);
			(*PObj)->TryGetBoolField(TEXT("owned"), P.bOwned);
			(*PObj)->TryGetNumberField(TEXT("accum"), P.Accum);
			// 'failed' and 'performance' post-date some saves; the struct
			// defaults (false / neutral) are what the Python's own .get() falls
			// back to, so an old save reads identically on both sides.
			(*PObj)->TryGetBoolField(TEXT("failed"), P.bFailed);
			(*PObj)->TryGetNumberField(TEXT("performance"), P.Performance);
			(*PObj)->TryGetNumberField(TEXT("wear"), P.Wear);   // optional: 0 on older saves
			// Age. age_last_tier is read as OPTIONAL: absent means the lot has
			// never been measured, which takes the reset branch on its next
			// advance, and that is not the same as a recorded tier of 0.
			(*PObj)->TryGetNumberField(TEXT("age_ticks"), P.AgeTicks);
			int32 LastTier = 0;
			if ((*PObj)->TryGetNumberField(TEXT("age_last_tier"), LastTier))
			{
				P.AgeLastTier = LastTier;
			}

			// 'placement' is present only on player-placed lots (step 2).
			const TSharedPtr<FJsonObject>* PlacementObj = nullptr;
			if ((*PObj)->TryGetObjectField(TEXT("placement"), PlacementObj)
				&& PlacementObj != nullptr && PlacementObj->IsValid())
			{
				FLotPlacement L;
				(*PlacementObj)->TryGetNumberField(TEXT("x0"), L.X0);
				(*PlacementObj)->TryGetNumberField(TEXT("x1"), L.X1);
				(*PlacementObj)->TryGetStringField(TEXT("side"), L.Side);
				// ABSENT, not defaulted. v0 wrote no road_id, so the owner's real
				// save has four lots without the key, and a round trip must not
				// invent one for them - LotRoadId() applies the fallback at the
				// point of use instead. Losing that distinction here is what
				// would quietly rewrite the owner's save on first load.
				FString RoadId;
				if ((*PlacementObj)->TryGetStringField(TEXT("road_id"), RoadId))
				{
					L.RoadId = RoadId;
				}
				P.Placement = L;
			}
			S.Parcels.Add(Pair.Key, P);
		}
	}

	Out = MoveTemp(S);
	return true;
}

FString CityStateToJson(const FCityState& State)
{
	const TSharedRef<FJsonObject> Root = MakeShared<FJsonObject>();
	Root->SetNumberField(TEXT("money"), State.Money);
	Root->SetNumberField(TEXT("demand"), State.Demand);
	Root->SetNumberField(TEXT("trades_processed"), State.TradesProcessed);
	Root->SetNumberField(TEXT("goals_reached"), State.GoalsReached);

	const TSharedRef<FJsonObject> Parcels = MakeShared<FJsonObject>();
	// Sorted, so a save is stable under a re-write and a diff of two saves shows
	// what changed rather than how the map happened to hash.
	TArray<FString> Ids;
	State.Parcels.GetKeys(Ids);
	Ids.Sort([](const FString& A, const FString& B) { return A < B; });
	for (const FString& Id : Ids)
	{
		const FParcelState& P = State.Parcels[Id];
		const TSharedRef<FJsonObject> PObj = MakeShared<FJsonObject>();
		PObj->SetStringField(TEXT("rid"), P.Rid);
		PObj->SetNumberField(TEXT("tier"), P.Tier);
		PObj->SetNumberField(TEXT("width"), P.Width);
		PObj->SetBoolField(TEXT("owned"), P.bOwned);
		PObj->SetNumberField(TEXT("accum"), P.Accum);
		PObj->SetBoolField(TEXT("failed"), P.bFailed);
		PObj->SetNumberField(TEXT("performance"), P.Performance);
		PObj->SetNumberField(TEXT("wear"), P.Wear);
		PObj->SetNumberField(TEXT("age_ticks"), P.AgeTicks);
		// Written only when recorded, so a never-aged lot round-trips as one
		// rather than acquiring a tier it was never measured against.
		if (P.AgeLastTier.IsSet())
		{
			PObj->SetNumberField(TEXT("age_last_tier"), P.AgeLastTier.GetValue());
		}
		if (P.Placement.IsSet())
		{
			const FLotPlacement& L = P.Placement.GetValue();
			const TSharedRef<FJsonObject> LObj = MakeShared<FJsonObject>();
			LObj->SetNumberField(TEXT("x0"), L.X0);
			LObj->SetNumberField(TEXT("x1"), L.X1);
			LObj->SetStringField(TEXT("side"), L.Side);
			// The key is written only when the lot actually has one - see the
			// reader above for why absence is preserved rather than filled in.
			if (L.RoadId.IsSet())
			{
				LObj->SetStringField(TEXT("road_id"), L.RoadId.GetValue());
			}
			PObj->SetObjectField(TEXT("placement"), LObj);
		}
		Parcels->SetObjectField(Id, PObj);
	}
	Root->SetObjectField(TEXT("parcels"), Parcels);

	// The key is written even when empty: seed_state() declares it and readers
	// use it, so dropping it would break the Python side's own expectations.
	const TSharedRef<FJsonObject> Roads = MakeShared<FJsonObject>();
	TArray<FString> RoadIds;
	State.Roads.GetKeys(RoadIds);
	SortRoadIds(RoadIds);
	for (const FString& RoadId : RoadIds)
	{
		const FRoadSegment& Seg = State.Roads[RoadId];
		const TSharedRef<FJsonObject> RObj = MakeShared<FJsonObject>();
		// 'id' is written as well as being the key: the Python stores the road
		// dict whole, id included, and the two must not disagree.
		RObj->SetStringField(TEXT("id"), RoadId);
		TArray<TSharedPtr<FJsonValue>> Start;
		Start.Add(MakeShared<FJsonValueNumber>(Seg.StartX));
		Start.Add(MakeShared<FJsonValueNumber>(Seg.StartY));
		TArray<TSharedPtr<FJsonValue>> End;
		End.Add(MakeShared<FJsonValueNumber>(Seg.EndX));
		End.Add(MakeShared<FJsonValueNumber>(Seg.EndY));
		RObj->SetArrayField(TEXT("start"), Start);
		RObj->SetArrayField(TEXT("end"), End);
		RObj->SetStringField(TEXT("width_class"), Seg.WidthClass);
		// Written only when there IS one, so a straight road's entry is
		// byte-for-byte what it was before curves existed and the Python
		// oracle's own files still round-trip unchanged.
		if (!Seg.Path.IsEmpty())
		{
			RObj->SetStringField(TEXT("path"), Seg.Path);
		}
		Roads->SetObjectField(RoadId, RObj);
	}
	Root->SetObjectField(TEXT("roads"), Roads);

	return WriteJsonObject(Root);
}

} // namespace Stacktown

// -----------------------------------------------------------------------------

void UStacktownEconomy::Initialize(FSubsystemCollectionBase& Collection)
{
	Super::Initialize(Collection);
	SeedFresh();
	if (!Catalogue.IsValid())
	{
		Catalogue = MakeShared<Stacktown::FStaticCatalogue>();
	}
	// QUEUE ITEM 2: resolve the session's state file NOW, not on whoever reads
	// it first. Lazy resolution made the answer depend on timing - a marker
	// appearing between startup and the first read would decide the session.
	Stacktown::EStateSource Source;
	StatePathForSession(Source, true);
}

void UStacktownEconomy::Deinitialize()
{
	Super::Deinitialize();
}

void UStacktownEconomy::SetStatePath(const FString& InAbsolutePath)
{
	StatePath = InAbsolutePath;
}

void UStacktownEconomy::SetCatalogue(const TSharedPtr<Stacktown::ICatalogue>& InCatalogue)
{
	Catalogue = InCatalogue;
}

void UStacktownEconomy::SetStateOverride(const FString& InAbsolutePath)
{
	StateOverride = InAbsolutePath;
	// Re-resolve at once: the path was already decided at Initialize, and an
	// override that quietly did nothing would leave a lane on the owner's real
	// save while its own log line claimed otherwise.
	Stacktown::EStateSource Source;
	StatePathForSession(Source, true);
}

bool UStacktownEconomy::LoadRulesFromFile(FString& OutError)
{
	const FString Path = Stacktown::RulesFilePath();
	FString Text;
	if (!FFileHelper::LoadFileToString(Text, *Path))
	{
		OutError = FString::Printf(TEXT("rules file missing: %s"), *Path);
		UE_LOG(LogStacktown, Error, TEXT("%s"), *OutError);
		return false;
	}
	return LoadRules(Text, OutError);
}

bool UStacktownEconomy::LoadRules(const FString& JsonText, FString& OutError)
{
	Stacktown::FEconRules Parsed;
	if (!Stacktown::FEconRules::FromJson(JsonText, Parsed, OutError))
	{
		UE_LOG(LogStacktown, Error, TEXT("LoadRules refused: %s"), *OutError);
		return false;
	}
	Rules = Parsed;
	return true;
}

bool UStacktownEconomy::LoadState(FString& OutError)
{
	if (StatePath.IsEmpty())
	{
		return true;
	}
	if (!FPaths::FileExists(StatePath))
	{
		State = Stacktown::SeedState(Rules);
		return true;
	}
	FString Text;
	if (!FFileHelper::LoadFileToString(Text, *StatePath))
	{
		OutError = FString::Printf(TEXT("could not read %s"), *StatePath);
		return false;
	}
	return Stacktown::CityStateFromJson(Text, State, OutError);
}

bool UStacktownEconomy::SaveState() const
{
	if (StatePath.IsEmpty())
	{
		// The deliberate no-op. See the class comment: this port does not guess
		// at the owner's save.
		return true;
	}
	return FFileHelper::SaveStringToFile(Stacktown::CityStateToJson(State), *StatePath);
}

// --- Phase A: mirroring ------------------------------------------------------

bool UStacktownEconomy::MirrorFromFile(const FString& AbsolutePath, FString& OutError)
{
	if (!StatePath.IsEmpty())
	{
		// Two writers is the one failure this contract exists to prevent, so
		// this refuses rather than quietly preferring one role over the other.
		OutError = FString::Printf(
			TEXT("refusing to mirror: StatePath is set to '%s', so this subsystem owns a file"),
			*StatePath);
		UE_LOG(LogStacktown, Error, TEXT("%s"), *OutError);
		return false;
	}
	if (!FPaths::FileExists(AbsolutePath))
	{
		OutError = FString::Printf(TEXT("no state file at %s"), *AbsolutePath);
		return false;
	}
	FString Text;
	if (!FFileHelper::LoadFileToString(Text, *AbsolutePath))
	{
		OutError = FString::Printf(TEXT("could not read %s"), *AbsolutePath);
		return false;
	}
	// Parsed into a LOCAL first. The Python side rewrites this file whole, so a
	// read landing mid-write sees a truncated document; committing that would
	// blank every parcel for a frame.
	Stacktown::FCityState Parsed;
	if (!Stacktown::CityStateFromJson(Text, Parsed, OutError))
	{
		return false;
	}
	State = MoveTemp(Parsed);
	++MirrorSyncCount;
	return true;
}

Stacktown::FStatePathInputs UStacktownEconomy::GatherStatePathInputs() const
{
	Stacktown::FStatePathInputs In;
	In.Override = StateOverride;

	// Phase A paths are the PYTHON side's, because Phase A mirrors the file the
	// Python driver resolved. Phase B moves these under Saved/Stacktown/.
	const FString PythonDir = FPaths::Combine(FPaths::ProjectContentDir(), TEXT("Python"));
	In.DefaultStatePath = FPaths::Combine(PythonDir, TEXT("citystate.json"));
	In.TestStatePath    = FPaths::Combine(PythonDir, TEXT("citystate_test.json"));

	const FString MarkerPath = FPaths::Combine(PythonDir, TEXT("lane_pie.marker"));
	In.bMarkerExists = FPaths::FileExists(MarkerPath);
	if (In.bMarkerExists)
	{
		FFileHelper::LoadFileToString(In.MarkerContent, *MarkerPath);
	}

	// Editor subsystems do not exist in a standalone game process, which is the
	// same distinction the Python makes; only an EDITOR session steps aside for
	// the lock.
	In.bIsGameProcess = !GIsEditor;

	const FString LockPath = FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("standalone.lock"));
	FString LockText;
	if (FFileHelper::LoadFileToString(LockText, *LockPath))
	{
		const uint32 Pid = static_cast<uint32>(FCString::Atoi(*LockText.TrimStartAndEnd()));
		// A stale lock from a crashed process must not steer anyone: liveness is
		// checked, not assumed from the file existing.
		In.bStandalonePidAlive = Pid != 0
			&& Pid != FPlatformProcess::GetCurrentProcessId()
			&& FPlatformProcess::IsApplicationRunning(Pid);
	}
	return In;
}

FString UStacktownEconomy::StatePathForSession(Stacktown::EStateSource& OutSource, bool bForceReresolve)
{
	if (bSessionPathResolved && !bForceReresolve)
	{
		OutSource = CachedSessionSource;
		return CachedSessionPath;
	}
	const Stacktown::FStatePathResolution R = Stacktown::ResolveStatePath(GatherStatePathInputs());
	CachedSessionPath = R.Path;
	CachedSessionSource = R.Source;
	bSessionPathResolved = true;
	OutSource = R.Source;
	// The source label is the audit trail: a lane that forgot its marker shows
	// "default" against its own session here.
	UE_LOG(LogStacktown, Log, TEXT("state path for session: %s (%s)"),
		*R.Path, *Stacktown::StateSourceName(R.Source));
	return R.Path;
}

void UStacktownEconomy::CityTick()
{
	TArray<Stacktown::FEconEvent> Events;
	// Tick, then age (queue item 7) - ONE composite, Stacktown::TickCity, shared
	// with the tests that predict what this call persists. Age stays outside
	// Tick itself so the economy oracles' exact known answers hold.
	const Stacktown::FPlacementBoard Board = Stacktown::FPlacementBoard::Default(Rules);   // the roads around each placed lot multiply its rent
	Stacktown::TickCity(Rules, State, Events, &Board);
	LastTickEvents.Append(Events);
	SaveState();
}

bool UStacktownEconomy::CityBuy(const FString& Pid, FString& OutReason)
{
	const Stacktown::FVerbResult R = Stacktown::Buy(Rules, State, Pid);
	OutReason = R.Reason;
	if (R.bOk)
	{
		SaveState();
	}
	return R.bOk;
}

bool UStacktownEconomy::CityUpgrade(const FString& Pid, FString& OutReason)
{
	check(Catalogue.IsValid());
	const Stacktown::FVerbResult R = Stacktown::Upgrade(Rules, *Catalogue, State, Pid);
	OutReason = R.Reason;
	if (R.bOk)
	{
		SaveState();
	}
	return R.bOk;
}

bool UStacktownEconomy::CityRepair(const FString& Pid, FString& OutReason)
{
	const Stacktown::FVerbResult R = Stacktown::Repair(Rules, State, Pid);
	OutReason = R.Reason;
	if (R.bOk)
	{
		SaveState();
	}
	return R.bOk;
}

bool UStacktownEconomy::EnsureParcel(const FString& Pid, const FString& Rid, double Width)
{
	if (State.Parcels.Contains(Pid))
	{
		return false;
	}
	Stacktown::FParcelState P;
	P.Rid = Rid;
	P.Tier = 0;          // ALWAYS. See the header.
	P.Width = Width;
	P.bOwned = false;
	P.Accum = 0.0;
	P.bFailed = false;
	P.Performance = 0.0;
	State.Parcels.Add(Pid, P);
	SaveState();
	return true;
}

void UStacktownEconomy::ResetCity()
{
	State = Stacktown::SeedState(Rules);
	SaveState();
	UE_LOG(LogStacktown, Warning,
		TEXT("CITYSTATE RESET: state wiped, reseeded from money_start=%.1f"), State.Money);
}

void UStacktownEconomy::ApplyTradeLedger(const TArray<double>& LedgerPnls,
	TArray<Stacktown::FEconEvent>& OutEvents)
{
	const int32 Before = State.TradesProcessed;
	Stacktown::ApplyTradeLedger(Rules, State, LedgerPnls, OutEvents);
	if (State.TradesProcessed != Before)
	{
		SaveState();
	}
}

void UStacktownEconomy::SetGoalsReached(int32 Rungs)
{
	if (State.GoalsReached == Rungs) { return; }
	State.GoalsReached = Rungs;
	SaveState();
}
