// UStacktownRuntimeSettings - the runtime switches, in Project Settings rather
// than only in an ini nobody can find (queue item 5).
//
// ONE SWITCH TODAY: bPythonDrivers. It decides whether the Python drivers still
// own the city or the C++ runtime does, and until Phase B it was readable only
// as a raw ini key and an environment variable.
//
// IT READS TWO INI SECTIONS, DELIBERATELY. A UDeveloperSettings class takes its
// section from its own name, so this one is
// [/Script/StacktownAlpha.StacktownRuntimeSettings] - but the switch already
// ships as [/Script/StacktownAlpha.StacktownRuntime] in Config/DefaultGame.ini,
// and Config/ is not this seat's to edit. So the resolver below checks the new
// section first and falls back to the legacy one, which means an existing
// install keeps working untouched and a value set through Project Settings wins
// over it. Delete the fallback when the ini key is migrated.
#pragma once

#include "CoreMinimal.h"
#include "Engine/DeveloperSettings.h"
#include "StacktownRuntimeSettings.generated.h"

UCLASS(config = Game, defaultconfig, meta = (DisplayName = "Stacktown Runtime"))
class STACKTOWNALPHA_API UStacktownRuntimeSettings : public UDeveloperSettings
{
	GENERATED_BODY()

public:
	/** Whether the editor-only Python drivers still own the city.
	 *
	 *  A PACKAGED APP IGNORES THIS ENTIRELY: the Python plugin is UncookedOnly
	 *  and is not there at all, so the C++ side owns the city regardless. The
	 *  switch only means anything in an editor or an uncooked game. */
	UPROPERTY(EditAnywhere, config, Category = "Runtime",
		meta = (ToolTip = "Editor only. A packaged app has no Python plugin and always uses the C++ runtime."))
	bool bPythonDrivers = true;

	virtual FName GetCategoryName() const override { return TEXT("Plugins"); }

	/** The resolved answer, in priority order:
	 *    1. no Python plugin loaded  -> false, whatever anything says;
	 *    2. STACKTOWN_PYTHON_DRIVERS in the environment;
	 *    3. this class's own ini section;
	 *    4. the legacy [/Script/StacktownAlpha.StacktownRuntime] section;
	 *    5. true.
	 *
	 *  Sections 3 and 4 are read through GConfig rather than off this object,
	 *  so "absent" and "present and false" stay distinguishable - a config
	 *  UPROPERTY silently keeps its C++ default when the key is missing, which
	 *  would make the legacy fallback unreachable. */
	static bool PythonDriversEnabled();

	/** Just the two ini sections plus the default, without the plugin and
	 *  environment checks. Exposed so the precedence is testable on its own. */
	static bool ReadPythonDriversFromConfig(bool& bOutFoundInNewSection,
		bool& bOutFoundInLegacySection);
};
