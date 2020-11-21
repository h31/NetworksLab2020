workspace "Network2020"
	architecture "x64"
	startproject "Server"

	configurations
	{
		"Debug",
		"Release",
		"Dist"
	}

outputdir = "%{cfg.buildcfg}-%{cfg.system}-%{cfg.architecture}"

--Include directories relative to root folder (solution directory)
--IncludeDir = {}
--IncludeDir["GLFW"] = "Vipera/vendor/GLFW/include"

project "DHCP_Server"
	location "DHCP_Server"
	kind "ConsoleApp" --SharedLib for dll or StaticLib for static
	language "C++"
	cppdialect "C++17"
	--staticruntime "on" --staticruntime off for dll

	targetdir ("bin/" .. outputdir .. "/%{prj.name}")
	objdir ("bin-int/" .. outputdir .. "/%{prj.name}")

	files
	{
		"%{prj.name}/src/**.h",
		"%{prj.name}/src/**.cpp",
		"%{prj.name}/src/**.c"
	}

	defines 
	{
		"_CRT_SECURE_NO_WARNINGS"
	}

	includedirs
	{
		"%{prj.name}/src",
		"vendor/crossplatform",
		"vendor/threading"
	}

	links 
	{ 
		"kernel32.lib",
		"user32.lib",
		"gdi32.lib",
		"winspool.lib",
		"comdlg32.lib",
		"advapi32.lib",
		"shell32.lib",
		"ole32.lib",
		"oleaut32.lib",
		"uuid.lib",
		"odbc32.lib",
		"odbccp32.lib"
	}

	filter "system:windows"
		systemversion "latest"

		defines
		{
			"WinSockApp",
			"UNICODE",
			"_UNICODE"
		}

		links 
		{
			"Ws2_32.lib"
		}
		
		--postbuildcommands
		--{
		--	("{COPY} %{cfg.buildtarget.relpath} \"../bin/" .. outputdir .. "/Sandbox/\"")
		--}

	filter "configurations:Debug"
		defines "SERVER_DEBUG"
		runtime "Debug"
		symbols "on"

	filter "configurations:Release"
		defines ""
		runtime "Release"
		optimize "on"

	filter "configurations:Dist"
		defines ""
		runtime "Release"
		optimize "on"

project "TFTP_Server"
	location "TFTP_Server"
	kind "ConsoleApp"
	language "C++"
	cppdialect "C++17"
	--staticruntime "on"

	targetdir ("bin/" .. outputdir .. "/%{prj.name}")
	objdir ("bin-int/" .. outputdir .. "/%{prj.name}")

	files
	{
		"%{prj.name}/src/**.h",
		"%{prj.name}/src/**.cpp",
		"%{prj.name}/src/**.c"
	}

	includedirs
	{
		"%{prj.name}/src",
		"vendor/crossplatform",
		"vendor/threading"
	}

	links
	{
		"kernel32.lib",
		"user32.lib",
		"gdi32.lib",
		"winspool.lib",
		"comdlg32.lib",
		"advapi32.lib",
		"shell32.lib",
		"ole32.lib",
		"oleaut32.lib",
		"uuid.lib",
		"odbc32.lib",
		"odbccp32.lib"
	}

	filter "system:windows"
		systemversion "latest"

		defines
		{
		    "WinSockApp",
			"UNICODE",
			"_UNICODE"
		}

		links 
		{
		    "Ws2_32.lib"
		}

	filter "configurations:Debug"
		defines "SERVER_DEBUG"
		runtime "Debug"
		symbols "on"

	filter "configurations:Release"
		defines ""
		runtime "Release"
		optimize "on"

	filter "configurations:Dist"
		defines ""
		runtime "Release"
		optimize "on"