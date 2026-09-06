using UnrealBuildTool;
using System.Collections.Generic;

public class StacktownAlphaTarget : TargetRules
{
	public StacktownAlphaTarget(TargetInfo Target) : base(Target)
	{
		Type = TargetType.Game;
		DefaultBuildSettings = BuildSettingsVersion.V7;
		IncludeOrderVersion = EngineIncludeOrderVersion.Unreal5_8;
		ExtraModuleNames.Add("StacktownAlpha");
	}
}
