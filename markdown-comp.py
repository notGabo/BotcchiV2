import os

def merge_project(root_dir,output_file):
    ignored_dirs = {'.venv', 'venv', '__pycache__', '.pytest_cache', '.mypy_cache', '.ruff_cache', '.cache'}
    with open(output_file, 'w',encoding='utf-8') as outfile:
        for root,dir, files in os.walk(root_dir):
            dir[:] = [name for name in dir if name not in ignored_dirs]
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    outfile.write(f"# File: {file_path}\n")
                    with open(file_path, 'r',encoding='utf-8') as infile:
                        outfile.write(infile.read())
                        outfile.write("\n\n")

merge_project('./src', 'src.md')
merge_project('.', 'main.md')
