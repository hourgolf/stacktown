#pragma once

#include "CoreMinimal.h"
#include "UObject/Object.h"
#include "StacktownHud.generated.h"

class UBorder;
class UHorizontalBox;
class UVerticalBox;
class USizeBox;
class USpacer;
class UTextBlock;
class UFont;
class UWidget;

/**
 * Everything the HUD says, as plain fields. Written by whoever owns the
 * facts (the Python drivers today, the C++ economy and input when they land)
 * and read by UStacktownHud every frame. A plain UObject on purpose: reflected
 * writes to it never re-run a construction script (HANDOFF §5, 2026-09-04).
 */
UCLASS(BlueprintType)
class STACKTOWNALPHA_API UStacktownHudModel : public UObject
{
	GENERATED_BODY()

public:
	// the bar
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|HUD") double Money = 0.0;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|HUD") double Demand = 0.0;
	/** PROPOSED score (StacktownScore.h) - on the bar for the design lane to rule on. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|HUD") double Score = 0.0;
	/** The next rung of the goal ladder; 0 when every rung is reached. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|HUD") double NextGoal = 0.0;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|HUD") bool bRoadMode = false;
	/** The road class drawn next while road mode is on; the mode word shows it. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|HUD") FString RoadClass = TEXT("avenue");
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|HUD") bool bNight = false;
	/** An action refusal (Docs/HUD_V1.md CONTENT 2): refuse colour, cleared on the next input. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|HUD") FString ActionRefusal;
	/** A dim bar message that is not a refusal (mode hints, the hold-N countdown). */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|HUD") FString BarMessage;
	/** True while the bar message is an announcement (label size, accept colour) rather than a status. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|HUD") bool bBarMessageAccent = false;

	// the selection panel (CONTENT 1, 4)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|HUD") bool bHasSelection = false;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|HUD") FString SelectedName;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|HUD") FString SelectedState;
	/** Empty when no verb is present; then the price line and verb row are absent. */
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|HUD") FString VerbKey;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|HUD") FString Verb;
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|HUD") double VerbPrice = 0.0;

	// at the cursor (LOOK 6): a place refusal next to the ghost
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|HUD") FString PlaceRefusal;

	// the legend (CONTENT 6, LOOK 5)
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|HUD")
	FString LegendCamera = TEXT("RIGHT-DRAG orbit      WHEEL zoom      EDGES or ARROWS pan");
	UPROPERTY(EditAnywhere, BlueprintReadWrite, Category = "Stacktown|HUD")
	FString LegendVerbs = TEXT("CLICK select / place      TAB width      B buy      U upgrade      H repair      N hold reset      G road mode");
};

/**
 * HUD v1 (Docs/HUD_V1.md), built in code and added through the game viewport
 * subsystem: the bar (top, full width), the selection panel (bottom-left,
 * 320 wide), the two-line legend (bottom-right) and a cursor refusal. One type
 * ramp, an 8 px grid, three colours and a ground; red only on a refusal.
 */
UCLASS()
class STACKTOWNALPHA_API UStacktownHud : public UObject
{
	GENERATED_BODY()

public:
	void Build(UWorld* World);
	void Apply(const UStacktownHudModel* Model, const FVector2D& CursorSlatePos, bool bCursorValid);
	void Teardown();
	bool IsBuilt() const { return Bar != nullptr; }

private:
	UPROPERTY() TObjectPtr<UWorld> World;
	UPROPERTY() TObjectPtr<UFont> SpaceMonoBold;
	UPROPERTY() TObjectPtr<UFont> TomorrowMedium;
	UPROPERTY() TObjectPtr<UFont> TomorrowSemiBold;

	UPROPERTY() TObjectPtr<UBorder> Bar;
	UPROPERTY() TObjectPtr<UTextBlock> MoneyText;
	UPROPERTY() TObjectPtr<UTextBlock> DemandLabel;
	UPROPERTY() TObjectPtr<UTextBlock> DemandText;
	UPROPERTY() TObjectPtr<UTextBlock> ScoreLabel;
	UPROPERTY() TObjectPtr<UTextBlock> ScoreText;
	UPROPERTY() TObjectPtr<UTextBlock> NextLabel;
	UPROPERTY() TObjectPtr<UTextBlock> NextText;
	UPROPERTY() TObjectPtr<UTextBlock> NextUnit;
	UPROPERTY() TObjectPtr<UTextBlock> BarMessageText;
	UPROPERTY() TObjectPtr<UTextBlock> RoadWord;
	UPROPERTY() TObjectPtr<UTextBlock> NightWord;

	UPROPERTY() TObjectPtr<USizeBox> PanelBox;
	UPROPERTY() TObjectPtr<UTextBlock> NameText;
	UPROPERTY() TObjectPtr<UTextBlock> StateText;
	UPROPERTY() TObjectPtr<UTextBlock> PriceText;
	UPROPERTY() TObjectPtr<USpacer> VerbGap;
	UPROPERTY() TObjectPtr<UHorizontalBox> VerbRow;
	UPROPERTY() TObjectPtr<UTextBlock> VerbKeyText;
	UPROPERTY() TObjectPtr<UTextBlock> VerbText;
	UPROPERTY() TObjectPtr<UTextBlock> VerbPriceText;

	UPROPERTY() TObjectPtr<UVerticalBox> LegendBox;
	UPROPERTY() TObjectPtr<UBorder> LegendRoot;
	UPROPERTY() TObjectPtr<UTextBlock> LegendCameraText;
	UPROPERTY() TObjectPtr<UTextBlock> LegendVerbsText;

	UPROPERTY() TObjectPtr<UTextBlock> CursorText;

	FSlateFontInfo Font(UFont* Face, float Size, int32 LetterSpacing = 0) const;
	UTextBlock* MakeText(UFont* Face, float Size, const FLinearColor& Colour, int32 LetterSpacing = 0);
	static void SetText(UTextBlock* T, const FString& S);
};
