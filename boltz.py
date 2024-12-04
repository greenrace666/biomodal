import os
from pathlib import Path
import modal
from modal import App, Image
import subprocess

vol = modal.Volume.from_name("boltz", create_if_missing=True)
GPU = "L4"

image = (
    Image.debian_slim(python_version="3.11")
    .pip_install("boltz")
)

app = App("boltz", image=image)

@app.function(gpu=GPU, volumes={"/root/.boltz": vol})
def boltz(input_faa_str: str, input_faa_name: str):
    from subprocess import run
    Path(in_dir := "./").mkdir(parents=True, exist_ok=True)
    Path(out_dir := "./").mkdir(parents=True, exist_ok=True)
    in_faa = Path(in_dir) / input_faa_name
    with open(in_faa, "w") as f:
        f.write(input_faa_str)

    try:
        run(
            [
                "boltz",
                "predict",
                str(in_faa),
                "--out_dir",
                str(out_dir),
                "--cache",
                "/root/.boltz",
                "--use_msa_server",
            ],
            check=True
        )
    except subprocess.CalledProcessError as e: 
        print(f"Error occurred: {e}") 
        return []
    vol.reload()
    return()
@app.function()
def list_files_and_contents(directory):
    files_and_contents = {}
    for file_path in Path(directory).iterdir():
        if file_path.is_file():
            with open(file_path, 'r') as file:
                files_and_contents[file_path.name] = file.read()
    return files_and_contents
def write_files_to_directory(files_and_contents, target_directory):
    Path(target_directory).mkdir(parents=True, exist_ok=True)
    for file_name, content in files_and_contents.items():
        target_path = Path(target_directory) / file_name
        with open(target_path, 'w') as file:
            file.write(content)
            return()
@app.local_entrypoint()
def main(input_faa: str,out_dir: str):
    input_faa_str = open(input_faa).read()
    boltz.remote(input_faa_str,Path(input_faa).name)
    current_directory = "./"
    target_directory = str(out_dir)
    write_files_to_directory(list_files_and_contents.remote(current_directory), target_directory)
    return()
