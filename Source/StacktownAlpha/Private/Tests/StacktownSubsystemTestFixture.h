// UE-only test scaffolding: a UStacktownEconomy standing on its own, with no
// running game around it. Extracted from StacktownCityStateTest.cpp when step 3
// needed the same thing, rather than copied - two copies of a fixture is how two
// suites start disagreeing about what they are testing.
#pragma once

#include "CoreMinimal.h"
#include "Engine/Engine.h"
#include "Engine/GameInstance.h"
#include "HAL/PlatformFileManager.h"
#include "Misc/FileHelper.h"
#include "Misc/Paths.h"
#include "UObject/StrongObjectPtr.h"
#include "StacktownEconomy.h"
#include "StacktownEconomyTestCommon.h"

namespace StacktownTest
{

/** State files go under Saved/SelfTest and nowhere else: citystate.json is the
 *  owner's save, and a self-test that writes production state is a bug. The
 *  filename is distinct from the Python's own throwaway so both suites can run
 *  at once without one clearing the other's file. */
inline FString SelfTestStatePath(const TCHAR* Leaf = TEXT("_selftest_citystate_cpp.json"))
{
	return FPaths::Combine(FPaths::ProjectSavedDir(), TEXT("SelfTest"), Leaf);
}

/** A subsystem with no running game around it.
 *
 *  IT STILL NEEDS A GAME INSTANCE FOR AN OUTER. UStacktownEconomy is a
 *  UGameInstanceSubsystem, so outering one to the transient package is rejected
 *  - which is what the first real-engine run of these tests found (27/28,
 *  Stacktown.CityState.Buy the one red). The pre-flight in Tools/preflight
 *  cannot see that class of defect at all: it never constructs a UObject.
 *
 *  GameInstance is declared FIRST deliberately: members initialise in
 *  declaration order, so it exists when Econ names it as its outer. Both are
 *  strong pointers so GC leaves the pair alone for a test's duration. */
struct FScopedEconomy
{
	TStrongObjectPtr<UGameInstance> GameInstance;
	TStrongObjectPtr<UStacktownEconomy> Econ;
	FString Path;

	explicit FScopedEconomy(bool bPersist = true,
		const TCHAR* Leaf = TEXT("_selftest_citystate_cpp.json"))
		: GameInstance(NewObject<UGameInstance>(GEngine))
		, Econ(NewObject<UStacktownEconomy>(GameInstance.Get()))
		, Path(SelfTestStatePath(Leaf))
	{
		IPlatformFile& File = FPlatformFileManager::Get().GetPlatformFile();
		File.CreateDirectoryTree(*FPaths::GetPath(Path));
		File.DeleteFile(*Path);   // a stale file from a previous run is a lie

		Econ->SetRules(OracleRules());
		Econ->SetCatalogue(OracleCatalogue());
		Econ->SeedFresh();
		if (bPersist)
		{
			Econ->SetStatePath(Path);
		}
	}

	~FScopedEconomy()
	{
		FPlatformFileManager::Get().GetPlatformFile().DeleteFile(*Path);
	}

	UStacktownEconomy* operator->() const { return Econ.Get(); }

	/** What is actually on disk right now, parsed back. */
	bool ReloadFromDisk(Stacktown::FCityState& Out, FString& OutError) const
	{
		FString Text;
		if (!FFileHelper::LoadFileToString(Text, *Path))
		{
			OutError = FString::Printf(TEXT("no file at %s"), *Path);
			return false;
		}
		return Stacktown::CityStateFromJson(Text, Out, OutError);
	}

	bool FileExists() const { return FPaths::FileExists(Path); }

	bool WriteRaw(const FString& Text) const
	{
		return FFileHelper::SaveStringToFile(Text, *Path);
	}
};

} // namespace StacktownTest
