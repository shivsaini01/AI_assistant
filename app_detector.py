import os
import shutil
import winreg


# =========================================================
# WINDOWS APPLICATION DETECTOR
# =========================================================

def find_in_path(executable_names):
    """
    Search for an executable available in Windows PATH.
    """

    for name in executable_names:
        path = shutil.which(name)

        if path:
            return os.path.abspath(path)

    return None


def find_from_registry(app_names):
    """
    Search Windows uninstall registry entries for an app.
    """

    registry_locations = [
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
        ),
        (
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
        ),
        (
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
        ),
    ]

    for root, registry_path in registry_locations:

        try:
            with winreg.OpenKey(
                root,
                registry_path
            ) as key:

                for i in range(
                    winreg.QueryInfoKey(key)[0]
                ):

                    try:
                        subkey_name = winreg.EnumKey(
                            key,
                            i
                        )

                        with winreg.OpenKey(
                            key,
                            subkey_name
                        ) as subkey:

                            display_name = ""

                            try:
                                display_name = winreg.QueryValueEx(
                                    subkey,
                                    "DisplayName"
                                )[0]
                            except FileNotFoundError:
                                pass

                            if not display_name:
                                continue

                            for app_name in app_names:

                                if app_name.lower() in str(
                                    display_name
                                ).lower():

                                    # Try InstallLocation first.
                                    try:
                                        install_location = winreg.QueryValueEx(
                                            subkey,
                                            "InstallLocation"
                                        )[0]

                                        if install_location:
                                            return install_location

                                    except FileNotFoundError:
                                        pass

                                    # Try DisplayIcon.
                                    try:
                                        display_icon = winreg.QueryValueEx(
                                            subkey,
                                            "DisplayIcon"
                                        )[0]

                                        if display_icon:
                                            return display_icon

                                    except FileNotFoundError:
                                        pass

                    except (
                        OSError,
                        FileNotFoundError
                    ):
                        continue

        except (
            OSError,
            FileNotFoundError
        ):
            continue

    return None


# =========================================================
# BRAVE
# =========================================================

def find_brave():

    path = find_in_path(
        [
            "brave.exe"
        ]
    )

    if path:
        return path

    possible_paths = [
        os.path.expandvars(
            r"%PROGRAMFILES%\BraveSoftware\Brave-Browser\Application\brave.exe"
        ),
        os.path.expandvars(
            r"%PROGRAMFILES(X86)%\BraveSoftware\Brave-Browser\Application\brave.exe"
        ),
        os.path.expandvars(
            r"%LOCALAPPDATA%\BraveSoftware\Brave-Browser\Application\brave.exe"
        ),
    ]

    for path in possible_paths:

        if os.path.isfile(path):
            return path

    return None


# =========================================================
# OBS
# =========================================================

def find_obs():

    path = find_in_path(
        [
            "obs64.exe",
            "obs32.exe",
            "obs.exe"
        ]
    )

    if path:
        return path

    possible_paths = [
        os.path.expandvars(
            r"%PROGRAMFILES%\obs-studio\bin\64bit\obs64.exe"
        ),
        os.path.expandvars(
            r"%PROGRAMFILES(X86)%\obs-studio\bin\32bit\obs32.exe"
        ),
    ]

    for path in possible_paths:

        if os.path.isfile(path):
            return path

    registry_path = find_from_registry(
        [
            "OBS Studio"
        ]
    )

    if registry_path:

        if os.path.isfile(registry_path):
            return registry_path

        possible_exe = os.path.join(
            registry_path,
            "bin",
            "64bit",
            "obs64.exe"
        )

        if os.path.isfile(possible_exe):
            return possible_exe

    return None




# =========================================================
# GENERIC APP DETECTOR
# =========================================================

def find_app(app_name):
    app_name = app_name.lower().strip()

    if app_name == "brave":
        return find_brave()

    if app_name == "obs":
        return find_obs()

    return None


# =========================================================
# TEST
# =========================================================

if __name__ == "__main__":

    print("=" * 50)
    print("JARVIS APPLICATION DETECTOR")
    print("=" * 50)

    applications = [
        "brave",
        "obs"
    ]

    for app in applications:

        path = find_app(app)

        if path:
            print(
                f"[FOUND] {app}:"
            )
            print(
                f"        {path}"
            )

        else:
            print(
                f"[NOT FOUND] {app}"
            )

    print("=" * 50)