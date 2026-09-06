#include "StacktownRuntimeSettings.h"

#include "StacktownAlpha.h"
#include "StacktownStateHandover.h"
#include "Misc/ConfigCacheIni.h"
#include "Misc/CoreMisc.h"
#include "HAL/PlatformMisc.h"
#include "Modules/ModuleManager.h"

namespace
{
	const TCHAR* NewSection    = TEXT("/Script/StacktownAlpha.StacktownRuntimeSettings");
	const TCHAR* LegacySection = TEXT("/Script/StacktownAlpha.StacktownRuntime");
}

bool UStacktownRuntimeSettings::ReadPythonDriversFromConfig(
	bool& bOutFoundInNewSection, bool& bOutFoundInLegacySection)
{
	bOutFoundInNewSection = false;
	bOutFoundInLegacySection = false;
	if (GConfig == nullptr)
	{
		return true;
	}
	bool bValue = true;
	if (GConfig->GetBool(NewSection, TEXT("bPythonDrivers"), bValue, GGameIni))
	{
		bOutFoundInNewSection = true;
		return bValue;
	}
	if (GConfig->GetBool(LegacySection, TEXT("bPythonDrivers"), bValue, GGameIni))
	{
		bOutFoundInLegacySection = true;
		return bValue;
	}
	return true;
}

bool UStacktownRuntimeSettings::PythonDriversEnabled()
{
	// This function only GATHERS; the precedence itself is
	// Stacktown::ResolvePythonDrivers, which is pure and exhaustively tested.
	Stacktown::FPythonDriversInputs In;
	In.bPluginLoaded = FModuleManager::Get().IsModuleLoaded(TEXT("PythonScriptPlugin"));
	In.EnvValue = FPlatformMisc::GetEnvironmentVariable(TEXT("STACKTOWN_PYTHON_DRIVERS"));

	bool bNewFound = false, bLegacyFound = false;
	const bool bConfigValue = ReadPythonDriversFromConfig(bNewFound, bLegacyFound);
	In.bFoundInNewSection = bNewFound;
	In.bFoundInLegacySection = bLegacyFound;
	In.bNewSectionValue = bConfigValue;
	In.bLegacySectionValue = bConfigValue;

	if (bLegacyFound && !bNewFound)
	{
		UE_LOG(LogStacktown, Verbose,
			TEXT("bPythonDrivers read from the legacy ini section; migrate it to %s"), NewSection);
	}
	return Stacktown::ResolvePythonDrivers(In);
}
