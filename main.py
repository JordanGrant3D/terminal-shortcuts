#!/home/jordan/Documents/terminal-shortcuts/venv/bin/python
from prompt_toolkit import Application
from prompt_toolkit.document import Document
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import HSplit, Layout, Window
from prompt_toolkit.styles import Style
from prompt_toolkit.widgets import TextArea
import glob
import subprocess
from pathlib import Path
import ast
import hashlib
import json

shortcuts = glob.glob("tshort/**/*.py", recursive=True)
json_path = Path("tshort/config.json")
current_path_check_index = 0
checked_paths = False
waiting_for_import_agree = False
current_json = {
    "paths": [],
    "hashes": [],
    "disabled": [],
    "disabled_reasons": {}
}
paths_to_verify = []

def main():
    handle_json()
    
    global current_path_check_index, waiting_for_import_agree, checked_paths, shortcuts, paths_to_verify
    invalid_shortcut = False

    # 1. Scrollable output panel at the top
    output_field = TextArea(
        text=(
            "--- Custom Terminal UI ---\nType a shortcut or text below and press 'Enter'"
            " \nType '_q' to quit."
            " \nType '_h' for help.\n"
            ),
        read_only=True,
        scrollbar=True,
    )

    # Show startup summary of any already-disabled shortcuts and their reasons
    disabled_list = current_json.get("disabled", [])
    disabled_reasons = current_json.get("disabled_reasons", {})
    if disabled_list:
        output_field.text += f"\n--- Notice: Disabled Shortcuts ---"
        for d_shortcut in disabled_list:
            reason = disabled_reasons.get(d_shortcut, "Unknown reason")
            output_field.text += f"\n • {Path(d_shortcut).name}: {reason}"
        output_field.text += f"\n-----------------------------------\n"

    for shortcut in shortcuts:
        if Path(shortcut).name in ["_ls.py", "_q.py", "_l.py", "_h.py"]:
            output_field.text += f"\n[Error] restricted shortcut name, you may not name a shortcut '_q', '_ls', '_h', or '_l'"
            invalid_shortcut = True

    if invalid_shortcut == False:
        active_paths_to_verify = [p for p in paths_to_verify if p not in current_json.get("disabled", [])]
        
        # Scan all files at once for errors upfront
        clean_paths_to_verify = []
        config_changed = False

        for file_name in active_paths_to_verify:
            try:
                get_imports(file_name)
                clean_paths_to_verify.append(file_name)
            except Exception as e:
                # Automatically disable files with syntax or read errors
                if file_name not in current_json["disabled"]:
                    current_json["disabled"].append(file_name)
                    current_json["disabled_reasons"][file_name] = f"Syntax/Read Error: {e}"
                    if file_name in current_json["paths"]:
                        idx = current_json["paths"].index(file_name)
                        current_json["paths"].pop(idx)
                        current_json["hashes"].pop(idx)
                    config_changed = True
                
                output_field.text += f"\n[Warning] Shortcut '{Path(file_name).name}' has a syntax/read error and was disabled:\n  -> {e}"

        # Save config once if any errors were found and disabled
        if config_changed:
            with open(json_path, "w", encoding="utf-8") as file:
                json.dump(current_json, file, indent=4)

        paths_to_verify = clean_paths_to_verify

        # Proceed with checking remaining valid paths
        if len(paths_to_verify) > 0 and current_path_check_index < len(paths_to_verify):
            file_name = paths_to_verify[current_path_check_index]
            output_field.text += f"\n\n{file_name} is requesting to import:"
            
            for req_import in get_imports(file_name):
                output_field.text += f"\n  - {req_import}"
            
            output_field.text += f"\nDo you accept these imports? (y/n): "
            waiting_for_import_agree = True
        else:
            checked_paths = True
            output_field.text += "\n\nAll paths checked!"

    # 2. Single-line input field fixed at the bottom
    input_field = TextArea(height=1, prompt="> ", multiline=False, wrap_lines=False)

    # 3. Handle what happens when the user presses Enter in the input field
    def accept_text(buff):
        global current_path_check_index, waiting_for_import_agree, checked_paths, shortcuts, paths_to_verify
        user_input = input_field.text.strip()
        
        if user_input == "_q":
            app.exit()
            return
            
        if invalid_shortcut == False:
            active_paths_to_verify = paths_to_verify
            
            if checked_paths == False:
                if waiting_for_import_agree:
                    if user_input.lower() == "y":
                        current_path_check_index += 1
                        waiting_for_import_agree = False
                        output_field.text += "\nAccepted."
                        shortcuts = glob.glob("tshort/**/*.py", recursive=True)

                    elif user_input.lower() == "n":
                        file_name = active_paths_to_verify[current_path_check_index]
                        
                        # Add to disabled list in JSON
                        if file_name not in current_json["disabled"]:
                            current_json["disabled"].append(file_name)
                            current_json["disabled_reasons"][file_name] = "Imports rejected by user"
                        
                        if file_name in current_json["paths"]:
                            idx = current_json["paths"].index(file_name)
                            current_json["paths"].pop(idx)
                            current_json["hashes"].pop(idx)
                        
                        # Save updated json immediately
                        with open(json_path, "w", encoding="utf-8") as file:
                            json.dump(current_json, file, indent=4)

                        waiting_for_import_agree = False
                        output_field.text += f"\nDisabled {Path(file_name).name}."
                        current_path_check_index += 1

                    # Check if we have more paths to verify
                    if current_path_check_index >= len(paths_to_verify):
                        checked_paths = True
                        output_field.text += "\n\nAll shortcuts checked!"
                    else:
                        file_name = paths_to_verify[current_path_check_index]
                        output_field.text += f"\n\n{file_name} is requesting to import:"
                        for req_import in get_imports(file_name):
                            output_field.text += f"\n  - {req_import}"
                        output_field.text += f"\nDo you accept these imports? (y/n): "
                        waiting_for_import_agree = True
            else:
                active_shortcuts = [s for s in shortcuts if s not in current_json.get("disabled", [])]

                # List active commands
                if user_input == "_ls":
                    output_field.text += f"\n--- Active Shortcuts ---"
                    for shortcut in active_shortcuts:
                        output_field.text += f"\n{Path(shortcut).stem}"
                    output_field.text += f"\n---"

                # List ALL commands (active + disabled) based on JSON status
                elif user_input == "_l":
                    output_field.text += f"\n--- All Shortcuts ---"
                    for shortcut in shortcuts:
                        p = Path(shortcut)
                        status = "[Disabled]" if shortcut in current_json.get("disabled", []) else "[Active]"
                        output_field.text += f"\n{p.stem} {status}"
                    output_field.text += f"\n---"

                elif user_input == "_h":
                    output_field.text += f"\n--- Help ---"
                    output_field.text += f"\n _l | list all active shortcuts"
                    output_field.text += f"\n _ls | list all shortcuts and their status"
                    output_field.text += f"\n _h | list help"
                    output_field.text += f"\n _q | exit program"
                    output_field.text += f"\n _e [shortcut] | try enable a shortcut"
                    output_field.text += f"\n _d [shortcut] | disable a shortcut"
                    output_field.text += f"\n---"

                # Manual disable command
                elif user_input.startswith("_d "):
                    target_name = user_input.replace("_d ", "").strip()
                    found = False
                    for shortcut in shortcuts:
                        p = Path(shortcut)
                        if p.stem == target_name:
                            found = True
                            if shortcut not in current_json["disabled"]:
                                current_json["disabled"].append(shortcut)
                                current_json["disabled_reasons"][shortcut] = "Manually disabled by user"
                                with open(json_path, "w", encoding="utf-8") as file:
                                    json.dump(current_json, file, indent=4)
                                output_field.text += f"\n[Success] Disabled shortcut: {target_name}"
                            else:
                                output_field.text += f"\n[Notice] Shortcut '{target_name}' is already disabled."
                            break
                    if not found:
                        output_field.text += f"\n[Error] Shortcut '{target_name}' not found."

                # Manual enable command
                elif user_input.startswith("_e "):
                    target_name = user_input.replace("_e ", "").strip()
                    found = False
                    for shortcut in shortcuts:
                        p = Path(shortcut)
                        if p.stem == target_name:
                            found = True
                            if shortcut in current_json["disabled"]:
                                # Extra safety: Test parsing before enabling back
                                try:
                                    get_imports(shortcut)
                                    current_json["disabled"].remove(shortcut)
                                    if shortcut in current_json["disabled_reasons"]:
                                        del current_json["disabled_reasons"][shortcut]
                                    with open(json_path, "w", encoding="utf-8") as file:
                                        json.dump(current_json, file, indent=4)
                                    handle_json()
                                    output_field.text += f"\n[Success] Enabled shortcut: {target_name}"
                                except Exception as e:
                                    output_field.text += f"\n[Error] Cannot enable '{target_name}', it still contains a syntax error: {e}"
                            else:
                                output_field.text += f"\n[Notice] Shortcut '{target_name}' is already enabled."
                            break
                    if not found:
                        output_field.text += f"\n[Error] Shortcut '{target_name}' not found."

                elif user_input:
                    executed = False
                    for shortcut in active_shortcuts:
                        if user_input == Path(shortcut).stem:
                            executed = True
                            has_error = False
                            error_message = ""
                            try:
                                result = subprocess.run(
                                    ["python3", f"{shortcut}"], 
                                    capture_output=True, 
                                    text=True, 
                                    timeout=15
                                )
                                if result.stdout:
                                    output_field.text += "\n" + result.stdout
                                
                                if result.returncode != 0:
                                    has_error = True
                                    error_message = result.stderr if result.stderr else f"Process exited with error code {result.returncode}"
                            except subprocess.TimeoutExpired:
                                has_error = True
                                error_message = f"Command '{user_input}' timed out after 15 seconds."
                            except Exception as e:
                                has_error = True
                                error_message = str(e)

                            if has_error:
                                if shortcut not in current_json["disabled"]:
                                    current_json["disabled"].append(shortcut)
                                    current_json["disabled_reasons"][shortcut] = f"Runtime Error: {error_message}"
                                    with open(json_path, "w", encoding="utf-8") as file:
                                        json.dump(current_json, file, indent=4)
                                
                                output_field.text += f"\n[Runtime Error in {Path(shortcut).name}]:\n{error_message}"
                                output_field.text += f"\n[Notice] Shortcut '{Path(shortcut).stem}' has been automatically disabled due to an error."
                            else:
                                if result.stderr:
                                    output_field.text += f"\n[Stderr in {Path(shortcut).name}]:\n{result.stderr}"
                    
                    if not executed:
                        output_field.text += f"\n[Error]: Unknown or disabled command '{user_input}'. Type '_l' to list commands."

        input_field.text = ""
        output_field.buffer.cursor_position = len(output_field.buffer.text)

    input_field.accept_handler = accept_text

    # 4. Layout structure
    container = HSplit(
        [
            output_field,
            Window(height=1, char="-", style="class:line"),
            input_field,
        ]
    )

    # Optional styling
    style = Style([("line", "#555555")])

    # 6. Initialize and run the full-screen application
    app = Application(
        layout=Layout(container, focused_element=input_field),
        style=style,
        full_screen=True,
        mouse_support=True,
    )
    app.run()


def get_imports(file_path):
    """Parses a Python file and returns a list of imported modules."""
    path = Path(file_path)

    with open(path, "r", encoding="utf-8") as f:
        tree = ast.parse(f.read(), filename=str(path))

    imported_modules = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imported_modules.add(alias.name)
        elif isinstance(node, ast.ImportFrom):
            if node.module:
                imported_modules.add(node.module)

    return sorted(list(imported_modules))


def get_file_hash(file_path, algorithm="sha256"):
    """Calculates and returns the hash of a file."""
    hash_func = hashlib.new(algorithm)
    with open(file_path, "rb") as file:
        while chunk := file.read(4096):
            hash_func.update(chunk)
    return hash_func.hexdigest()


def handle_json():
    global current_json, paths_to_verify
    stored_paths = []
    stored_hashes = []
    stored_disabled = []
    stored_reasons = {}
    
    if json_path.exists():
        with open(json_path, "r", encoding="utf-8") as file:
            data = json.load(file)
            stored_paths = data.get("paths", [])
            stored_hashes = data.get("hashes", [])
            stored_disabled = data.get("disabled", [])
            stored_reasons = data.get("disabled_reasons", {})
    
    current_json["disabled"] = stored_disabled
    current_json["disabled_reasons"] = stored_reasons
    old_hash_map = dict(zip(stored_paths, stored_hashes))
    
    final_paths = []
    final_hashes = []
    
    for shortcut in shortcuts:
        shortcut_path = Path(shortcut)
        if not shortcut_path.exists():
            continue
            
        curr_hash = get_file_hash(shortcut)
        final_paths.append(shortcut)
        final_hashes.append(curr_hash)
        
        # Only verify if it's a new file or if the hash has changed
        if shortcut not in old_hash_map or old_hash_map[shortcut] != curr_hash:
            paths_to_verify.append(shortcut)
            
    current_json["paths"] = final_paths
    current_json["hashes"] = final_hashes
    
    json_path.parent.mkdir(parents=True, exist_ok=True)
    with open(json_path, "w", encoding="utf-8") as file:
        json.dump(current_json, file, indent=4)


if __name__ == "__main__":
    main()

