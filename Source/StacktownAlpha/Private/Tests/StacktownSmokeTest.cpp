// Phase 0 proof that the command-line test loop works before any port lands:
//   UnrealEditor-Cmd <uproject> -ExecCmds="Automation RunTests Stacktown.Smoke; Quit" -unattended -nullrhi
// Every ported module adds its tests beside this one, named Stacktown.<Area>.<Case>.
#include "Misc/AutomationTest.h"
#include "StacktownAlpha.h"

#if WITH_DEV_AUTOMATION_TESTS

IMPLEMENT_SIMPLE_AUTOMATION_TEST(FStacktownSmokeModuleTest, "Stacktown.Smoke.ModuleLinked",
	EAutomationTestFlags::EditorContext | EAutomationTestFlags::ProductFilter)

bool FStacktownSmokeModuleTest::RunTest(const FString& Parameters)
{
	UE_LOG(LogStacktown, Log, TEXT("Stacktown.Smoke: the game module is linked and its log category is live"));
	TestTrue(TEXT("module linked"), FModuleManager::Get().IsModuleLoaded(TEXT("StacktownAlpha")));
	return true;
}

#endif
