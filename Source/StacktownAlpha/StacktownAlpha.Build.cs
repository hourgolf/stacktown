using UnrealBuildTool;

// The shipping runtime for Stacktown (Docs/PLAN_CPP_PORT.md). Gameplay that
// lived in Content/Python (editor-only, cannot cook) is ported here module by
// module; the Python drivers stay as the specification and the test oracle.
public class StacktownAlpha : ModuleRules
{
	public StacktownAlpha(ReadOnlyTargetRules Target) : base(Target)
	{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;

		PublicDependencyModuleNames.AddRange(new string[] {
			"Core", "CoreUObject", "Engine", "InputCore", "EnhancedInput",
			"Json", "JsonUtilities", "DeveloperSettings",
			"UMG", "Slate", "SlateCore"
		});

		// ProceduralMeshComponent: a drawn road is a mitred slab built per chord
		// (StacktownRoad.cpp) - a stock cube cannot be cut on the bias.
		PrivateDependencyModuleNames.AddRange(new string[] { "ProceduralMeshComponent" });
	}
}
