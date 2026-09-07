#include "StacktownHud.h"
#include "StacktownAlpha.h"
#include "Blueprint/GameViewportSubsystem.h"
#include "Components/Border.h"
#include "Components/HorizontalBox.h"
#include "Components/HorizontalBoxSlot.h"
#include "Components/SizeBox.h"
#include "Components/Spacer.h"
#include "Components/TextBlock.h"
#include "Components/VerticalBox.h"
#include "Components/VerticalBoxSlot.h"
#include "Engine/Font.h"
#include "Engine/World.h"
#include "Engine/Engine.h"
#include "Fonts/SlateFontInfo.h"

namespace
{
	// LOOK 4: three colours and a ground, from the board's own palette.
	const FLinearColor Ink = FLinearColor::FromSRGBColor(FColor(0xE8, 0xE0, 0xD4));
	const FLinearColor Dim = FLinearColor::FromSRGBColor(FColor(0x9A, 0x91, 0x87));
	const FLinearColor Accept = FLinearColor::FromSRGBColor(FColor(0xC0, 0x8A, 0x4E));
	const FLinearColor Refuse = FLinearColor::FromSRGBColor(FColor(0xB4, 0x47, 0x2E));
	const FLinearColor Ground = FLinearColor(FLinearColor::FromSRGBColor(FColor(0x2A, 0x2A, 0x2E)).CopyWithNewOpacity(0.88f));

	// LOOK 2: the ramp. Five sizes and no others.
	constexpr float SizeDisplay = 34.f;
	constexpr float SizeTitle = 22.f;
	constexpr float SizeBody = 18.f;
	constexpr float SizeLabel = 15.f;
	constexpr float SizeMicro = 12.f;
	constexpr int32 SpacingLabel = 60;   // +0.06 em, in 1/1000 em
	constexpr int32 SpacingMicro = 80;   // +0.08 em

	// LOOK 3: the grid.
	constexpr float Margin = 32.f;
	constexpr float Pad = 16.f;
	constexpr float BarHeight = 76.f;
	constexpr float PanelWidth = 320.f;

	FString MoneyString(double V)
	{
		return FString::Printf(TEXT("$%s"), *FText::AsNumber((int64)FMath::RoundToDouble(V)).ToString());
	}
}

FSlateFontInfo UStacktownHud::Font(UFont* Face, float Size, int32 LetterSpacing) const
{
	FSlateFontInfo Info(Face, Size);
	Info.LetterSpacing = LetterSpacing;
	return Info;
}

UTextBlock* UStacktownHud::MakeText(UFont* Face, float Size, const FLinearColor& Colour, int32 LetterSpacing)
{
	UTextBlock* T = NewObject<UTextBlock>(this);
	T->SetFont(Font(Face, Size, LetterSpacing));
	T->SetColorAndOpacity(FSlateColor(Colour));
	T->SetText(FText::GetEmpty());
	return T;
}

void UStacktownHud::SetText(UTextBlock* T, const FString& S)
{
	if (T && !T->GetText().ToString().Equals(S))
	{
		T->SetText(FText::FromString(S));
	}
}

void UStacktownHud::Build(UWorld* InWorld)
{
	World = InWorld;
	UGameViewportSubsystem* VS = (World && GEngine) ? GEngine->GetEngineSubsystem<UGameViewportSubsystem>() : nullptr;
	if (!VS)
	{
		UE_LOG(LogStacktown, Warning, TEXT("StacktownHud: no game viewport subsystem; HUD not built"));
		return;
	}
	// The font trap (board, LOOK seat 2026-09-05): bind the *_Font assets, never the F_* faces.
	SpaceMonoBold = LoadObject<UFont>(nullptr, TEXT("/Game/Stacktown/UI/Fonts/SpaceMono-Bold_Font.SpaceMono-Bold_Font"));
	TomorrowMedium = LoadObject<UFont>(nullptr, TEXT("/Game/Stacktown/UI/Fonts/Tomorrow-Medium_Font.Tomorrow-Medium_Font"));
	TomorrowSemiBold = LoadObject<UFont>(nullptr, TEXT("/Game/Stacktown/UI/Fonts/Tomorrow-SemiBold_Font.Tomorrow-SemiBold_Font"));
	if (!SpaceMonoBold || !TomorrowMedium || !TomorrowSemiBold)
	{
		UE_LOG(LogStacktown, Warning, TEXT("StacktownHud: a font asset failed to load (mono %d medium %d semibold %d)"), SpaceMonoBold != nullptr, TomorrowMedium != nullptr, TomorrowSemiBold != nullptr);
	}

	// ---- the bar: top, full width, 76 px, ground; left cluster at 32, right cluster ending at -32
	Bar = NewObject<UBorder>(this);
	Bar->SetBrushColor(Ground);
	Bar->SetPadding(FMargin(Margin, 0.f, Margin, 0.f));
	Bar->SetVerticalAlignment(VAlign_Fill);
	Bar->SetHorizontalAlignment(HAlign_Fill);
	UHorizontalBox* BarRow = NewObject<UHorizontalBox>(this);
	Bar->SetContent(BarRow);

	MoneyText = MakeText(SpaceMonoBold, SizeDisplay, Ink);
	if (UHorizontalBoxSlot* S = BarRow->AddChildToHorizontalBox(MoneyText)) { S->SetVerticalAlignment(VAlign_Center); }
	DemandLabel = MakeText(TomorrowMedium, SizeLabel, Dim, SpacingLabel);
	SetText(DemandLabel, TEXT("DEMAND"));
	if (UHorizontalBoxSlot* S = BarRow->AddChildToHorizontalBox(DemandLabel)) { S->SetVerticalAlignment(VAlign_Center); S->SetPadding(FMargin(24.f, 0.f, 0.f, 0.f)); }
	DemandText = MakeText(SpaceMonoBold, SizeBody, Ink);
	if (UHorizontalBoxSlot* S = BarRow->AddChildToHorizontalBox(DemandText)) { S->SetVerticalAlignment(VAlign_Center); S->SetPadding(FMargin(8.f, 0.f, 0.f, 0.f)); }
	// SCORE, PROPOSED (MONDAY_DECISIONS section 1): the same label + number pattern as
	// demand, 24 gap, so the left cluster stays "persistent facts only" (LOOK 5).
	ScoreLabel = MakeText(TomorrowMedium, SizeLabel, Dim, SpacingLabel);
	SetText(ScoreLabel, TEXT("SCORE"));
	if (UHorizontalBoxSlot* S = BarRow->AddChildToHorizontalBox(ScoreLabel)) { S->SetVerticalAlignment(VAlign_Center); S->SetPadding(FMargin(24.f, 0.f, 0.f, 0.f)); }
	ScoreText = MakeText(SpaceMonoBold, SizeBody, Ink);
	if (UHorizontalBoxSlot* S = BarRow->AddChildToHorizontalBox(ScoreText)) { S->SetVerticalAlignment(VAlign_Center); S->SetPadding(FMargin(8.f, 0.f, 0.f, 0.f)); }
	// NEXT goal (proposed): the number a stranger chases, beside the score.
	NextLabel = MakeText(TomorrowMedium, SizeLabel, Dim, SpacingLabel);
	SetText(NextLabel, TEXT("NEXT"));
	if (UHorizontalBoxSlot* S = BarRow->AddChildToHorizontalBox(NextLabel)) { S->SetVerticalAlignment(VAlign_Center); S->SetPadding(FMargin(24.f, 0.f, 0.f, 0.f)); }
	NextText = MakeText(SpaceMonoBold, SizeBody, Ink);
	if (UHorizontalBoxSlot* S = BarRow->AddChildToHorizontalBox(NextText)) { S->SetVerticalAlignment(VAlign_Center); S->SetPadding(FMargin(8.f, 0.f, 0.f, 0.f)); }
	NextUnit = MakeText(TomorrowMedium, SizeLabel, Dim, SpacingLabel);   // LOOK 4: NEXT  5,000  POINTS - number then its unit
	SetText(NextUnit, TEXT("POINTS"));
	if (UHorizontalBoxSlot* S = BarRow->AddChildToHorizontalBox(NextUnit)) { S->SetVerticalAlignment(VAlign_Center); S->SetPadding(FMargin(8.f, 0.f, 0.f, 0.f)); }
	BarMessageText = MakeText(TomorrowMedium, SizeBody, Dim);
	if (UHorizontalBoxSlot* S = BarRow->AddChildToHorizontalBox(BarMessageText)) { S->SetVerticalAlignment(VAlign_Center); S->SetPadding(FMargin(Margin, 0.f, 0.f, 0.f)); }
	USpacer* Fill = NewObject<USpacer>(this);
	if (UHorizontalBoxSlot* S = BarRow->AddChildToHorizontalBox(Fill)) { S->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); }
	RoadWord = MakeText(TomorrowMedium, SizeLabel, Dim, SpacingLabel);
	SetText(RoadWord, TEXT("ROAD"));
	if (UHorizontalBoxSlot* S = BarRow->AddChildToHorizontalBox(RoadWord)) { S->SetVerticalAlignment(VAlign_Center); S->SetPadding(FMargin(24.f, 0.f, 0.f, 0.f)); }
	NightWord = MakeText(TomorrowMedium, SizeLabel, Dim, SpacingLabel);
	SetText(NightWord, TEXT("NIGHT"));
	if (UHorizontalBoxSlot* S = BarRow->AddChildToHorizontalBox(NightWord)) { S->SetVerticalAlignment(VAlign_Center); S->SetPadding(FMargin(24.f, 0.f, 0.f, 0.f)); }
	SlotWord = MakeText(TomorrowMedium, SizeLabel, Dim, SpacingLabel);
	SetText(SlotWord, TEXT("SLOT 2"));
	if (UHorizontalBoxSlot* S = BarRow->AddChildToHorizontalBox(SlotWord)) { S->SetVerticalAlignment(VAlign_Center); S->SetPadding(FMargin(24.f, 0.f, 0.f, 0.f)); }
	RoadWord->SetVisibility(ESlateVisibility::Collapsed);
	NightWord->SetVisibility(ESlateVisibility::Collapsed);
	SlotWord->SetVisibility(ESlateVisibility::Collapsed);
	{
		FGameViewportWidgetSlot Slot;
		Slot.Anchors = FAnchors(0.f, 0.f, 1.f, 0.f);
		Slot.Offsets = FMargin(0.f, 0.f, 0.f, BarHeight);
		Slot.Alignment = FVector2D(0.f, 0.f);
		Slot.ZOrder = 10;
		VS->AddWidget(Bar, Slot);
	}
	Bar->SetVisibility(ESlateVisibility::HitTestInvisible);

	// ---- the selection panel: bottom-left, 320 wide, height by content, 16 padding
	PanelBox = NewObject<USizeBox>(this);
	PanelBox->SetWidthOverride(PanelWidth);
	UBorder* Panel = NewObject<UBorder>(this);
	Panel->SetBrushColor(Ground);
	Panel->SetPadding(FMargin(Pad));
	PanelBox->SetContent(Panel);
	UVerticalBox* Col = NewObject<UVerticalBox>(this);
	Panel->SetContent(Col);
	NameText = MakeText(TomorrowSemiBold, SizeTitle, Ink);
	Col->AddChildToVerticalBox(NameText);
	StateText = MakeText(TomorrowMedium, SizeBody, Ink);
	if (UVerticalBoxSlot* S = Col->AddChildToVerticalBox(StateText)) { S->SetPadding(FMargin(0.f, 8.f, 0.f, 0.f)); }
	PriceText = MakeText(SpaceMonoBold, SizeBody, Accept);
	PriceText->SetVisibility(ESlateVisibility::Collapsed);   // LOOK ruling 2026-09-06: the verb row carries the price; a standalone line read as a bug
	VerbGap = NewObject<USpacer>(this);
	VerbGap->SetSize(FVector2D(1.f, Pad));
	Col->AddChildToVerticalBox(VerbGap);
	VerbRow = NewObject<UHorizontalBox>(this);
	Col->AddChildToVerticalBox(VerbRow);
	VerbKeyText = MakeText(TomorrowMedium, SizeLabel, Dim, SpacingLabel);   // LOOK ruling: the cap tells you what to press
	if (UHorizontalBoxSlot* S = VerbRow->AddChildToHorizontalBox(VerbKeyText)) { S->SetVerticalAlignment(VAlign_Center); }
	VerbText = MakeText(TomorrowMedium, SizeBody, Ink);
	if (UHorizontalBoxSlot* S = VerbRow->AddChildToHorizontalBox(VerbText)) { S->SetVerticalAlignment(VAlign_Center); S->SetPadding(FMargin(16.f, 0.f, 0.f, 0.f)); }
	USpacer* VerbFill = NewObject<USpacer>(this);
	if (UHorizontalBoxSlot* S = VerbRow->AddChildToHorizontalBox(VerbFill)) { S->SetSize(FSlateChildSize(ESlateSizeRule::Fill)); }
	VerbPriceText = MakeText(SpaceMonoBold, SizeBody, Accept);
	VerbPriceText->SetJustification(ETextJustify::Right);
	if (UHorizontalBoxSlot* S = VerbRow->AddChildToHorizontalBox(VerbPriceText)) { S->SetVerticalAlignment(VAlign_Center); S->SetHorizontalAlignment(HAlign_Right); }
	{
		FGameViewportWidgetSlot Slot;
		Slot.Anchors = FAnchors(0.f, 1.f, 0.f, 1.f);
		Slot.Offsets = FMargin(Margin, -Margin, 0.f, 0.f);
		Slot.Alignment = FVector2D(0.f, 1.f);
		Slot.ZOrder = 10;
		VS->AddWidget(PanelBox, Slot);
	}
	PanelBox->SetVisibility(ESlateVisibility::Collapsed);

	// ---- the legend: bottom-right, two micro lines, dim, ending at -32
	LegendBox = NewObject<UVerticalBox>(this);
	UBorder* LegendScrim = NewObject<UBorder>(this);   // LOOK ruling: dim micro on a cream plate needs a ground
	LegendScrim->SetBrushColor(FLinearColor(FLinearColor::FromSRGBColor(FColor(0x2A, 0x2A, 0x2E)).CopyWithNewOpacity(0.88f)));   // LOOK 16:02: the SAME ground as the bar and panel; 0.45 was a second, arbitrary opacity and read as a muddy box over the day plate
	LegendScrim->SetPadding(FMargin(Pad));
	LegendScrim->SetContent(LegendBox);
	LegendCameraText = MakeText(TomorrowMedium, SizeMicro, Dim, SpacingMicro);
	LegendCameraText->SetJustification(ETextJustify::Right);
	if (UVerticalBoxSlot* S = LegendBox->AddChildToVerticalBox(LegendCameraText)) { S->SetHorizontalAlignment(HAlign_Right); }
	LegendVerbsText = MakeText(TomorrowMedium, SizeMicro, Dim, SpacingMicro);
	LegendVerbsText->SetJustification(ETextJustify::Right);
	if (UVerticalBoxSlot* S = LegendBox->AddChildToVerticalBox(LegendVerbsText)) { S->SetHorizontalAlignment(HAlign_Right); S->SetPadding(FMargin(0.f, 8.f, 0.f, 0.f)); }
	{
		FGameViewportWidgetSlot Slot;
		Slot.Anchors = FAnchors(1.f, 1.f, 1.f, 1.f);
		Slot.Offsets = FMargin(-Margin, -Margin, 0.f, 0.f);
		Slot.Alignment = FVector2D(1.f, 1.f);
		Slot.ZOrder = 10;
		VS->AddWidget(LegendScrim, Slot);
	}
	LegendScrim->SetVisibility(ESlateVisibility::HitTestInvisible);
	LegendRoot = LegendScrim;

	// ---- the cursor refusal: body, refuse, next to the ghost
	CursorText = MakeText(TomorrowMedium, SizeBody, Refuse);
	{
		FGameViewportWidgetSlot Slot;
		Slot.Anchors = FAnchors(0.f, 0.f, 0.f, 0.f);
		Slot.Offsets = FMargin(0.f, 0.f, 0.f, 0.f);
		Slot.Alignment = FVector2D(0.f, 0.f);
		Slot.ZOrder = 11;
		VS->AddWidget(CursorText, Slot);
	}
	CursorText->SetVisibility(ESlateVisibility::Collapsed);

	UE_LOG(LogStacktown, Log, TEXT("StacktownHud: built (bar, panel, legend, cursor)"));
}

void UStacktownHud::Apply(const UStacktownHudModel* M, const FVector2D& CursorSlatePos, bool bCursorValid)
{
	if (!M || !Bar)
	{
		return;
	}
	SetText(MoneyText, MoneyString(M->Money));
	SetText(DemandText, FString::Printf(TEXT("%.2f"), M->Demand));
	SetText(ScoreText, FText::AsNumber((int64)FMath::RoundToDouble(M->Score)).ToString());
	const bool bNext = M->NextGoal > 0.0;
	NextLabel->SetVisibility(bNext ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
	NextText->SetVisibility(bNext ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
	NextUnit->SetVisibility(bNext ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
	if (bNext) { SetText(NextText, FText::AsNumber((int64)M->NextGoal).ToString()); }
	// the bar's message slot: a refusal wins, in refuse; otherwise the dim message
	if (!M->ActionRefusal.IsEmpty())
	{
		BarMessageText->SetColorAndOpacity(FSlateColor(Refuse));
		SetText(BarMessageText, M->ActionRefusal);
	}
	else
	{
		BarMessageText->SetColorAndOpacity(FSlateColor(M->bBarMessageAccent ? Accept : Dim));
		SetText(BarMessageText, M->BarMessage);
	}
	RoadWord->SetVisibility(M->bRoadMode ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
	SetText(RoadWord, M->bRoadMode ? M->RoadClass.ToUpper() : FString(TEXT("ROAD")));   // LOOK 4: the type IS the mode word
	NightWord->SetVisibility(M->bNight ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
	// The slot word, like NIGHT: a state tag on the bar's right, only when it is not the default. Placeholder placement, the design lane's to move.
	SetText(SlotWord, FString::Printf(TEXT("SLOT %d"), M->Slot));
	SlotWord->SetVisibility(M->Slot > 1 ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);

	if (M->bHasSelection)
	{
		PanelBox->SetVisibility(ESlateVisibility::HitTestInvisible);
		SetText(NameText, M->SelectedName);
		SetText(StateText, M->SelectedState);
		const bool bVerb = !M->Verb.IsEmpty();
		const bool bAffordable = M->Money >= M->VerbPrice;
		const FLinearColor PriceColour = bAffordable ? Accept : Dim;
		VerbGap->SetVisibility(bVerb ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
		VerbRow->SetVisibility(bVerb ? ESlateVisibility::HitTestInvisible : ESlateVisibility::Collapsed);
		if (bVerb)
		{
			SetText(VerbKeyText, M->VerbKey);
			SetText(VerbText, M->Verb);
			VerbPriceText->SetColorAndOpacity(FSlateColor(PriceColour));
			SetText(VerbPriceText, MoneyString(M->VerbPrice));
		}
	}
	else
	{
		PanelBox->SetVisibility(ESlateVisibility::Collapsed);
	}

	SetText(LegendCameraText, M->LegendCamera);
	// Design lane 22:00: a legend, not a manual - only what is available now. The camera
	// line is always on; the verbs line follows the mode and the selection, exactly as
	// the verb row does. P (the starter city) lives in the fresh-city hint, not here.
	{
		FString Verbs;
		if (M->bRoadMode) { Verbs = TEXT("CLICK nodes      ENTER draw      BACKSPACE undo      T road type      G leave road mode"); }
		else if (M->bHasSelection && !M->Verb.IsEmpty()) { Verbs = FString::Printf(TEXT("%s %s      CLICK elsewhere      G road      L night      N hold reset"), *M->VerbKey, *M->Verb.ToLower()); }
		else if (M->bHasSelection) { Verbs = TEXT("CLICK elsewhere      G road      L night      N hold reset"); }
		else { Verbs = TEXT("CLICK place      TAB width      R building      G road      L night      N hold reset      1-3 slot"); }
		SetText(LegendVerbsText, Verbs);
	}

	if (!M->PlaceRefusal.IsEmpty() && bCursorValid)
	{
		SetText(CursorText, M->PlaceRefusal);
		CursorText->SetVisibility(ESlateVisibility::HitTestInvisible);
		if (UGameViewportSubsystem* VS = (World && GEngine) ? GEngine->GetEngineSubsystem<UGameViewportSubsystem>() : nullptr)
		{
			FGameViewportWidgetSlot Slot = VS->GetWidgetSlot(CursorText);
			Slot.Offsets = FMargin(CursorSlatePos.X + 24.f, CursorSlatePos.Y + 24.f, 0.f, 0.f);
			VS->SetWidgetSlot(CursorText, Slot);
		}
	}
	else
	{
		CursorText->SetVisibility(ESlateVisibility::Collapsed);
	}
}

void UStacktownHud::Teardown()
{
	if (UGameViewportSubsystem* VS = (World && GEngine) ? GEngine->GetEngineSubsystem<UGameViewportSubsystem>() : nullptr)
	{
		for (UWidget* W : TArray<UWidget*>{ Bar, PanelBox, LegendRoot, CursorText })
		{
			if (W) { VS->RemoveWidget(W); }
		}
	}
	Bar = nullptr;
}
