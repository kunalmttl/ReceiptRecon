import os
import ast

def get_project_name():
    return "ReceiptRecon"

def list_files_tree(start_path='.', prefix=''):
    tree = ''
    for root, dirs, files in os.walk(start_path):
        level = root.replace(start_path, '').count(os.sep)
        indent = ' ' * 4 * level
        tree += f"{indent}{os.path.basename(root)}/\n"
        sub_indent = ' ' * 4 * (level + 1)
        for f in files:
            if f != 'README.md':
                tree += f"{sub_indent}{f}\n"
        # skip hidden dirs like .git
        dirs[:] = [d for d in dirs if not d.startswith('.')]
    return tree

def extract_doc_summary():
    summary = ""
    for root, _, files in os.walk("."):
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read(), filename=path)
                        for node in ast.walk(tree):
                            if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and ast.get_docstring(node):
                                name = node.name
                                doc = ast.get_docstring(node).strip().split('\n')[0]
                                summary += f"- **{name}**: {doc}\n"
                except Exception:
                    continue
    return summary.strip()

def generate_readme():
    project_name = get_project_name()
    file_tree = list_files_tree()
    doc_summary = extract_doc_summary()

    # build README content
    readme = f"# {project_name}\n\n"
    readme += "## 📌 Project Overview\n\n"
    readme += (
        "ReceiptRecon is a Python-based OCR and data extraction tool designed to parse "
        "receipt images and extract structured information such as items, prices, totals, "
        "and merchant details. It utilizes image preprocessing, text detection, and NLP techniques "
        "to accurately understand receipt layouts.\n\n"
    )

    readme += "### 🔍 Features\n"
    readme += "- OCR-based text extraction from receipt images\n"
    readme += "- Line item parsing and total cost calculation\n"
    readme += "- Modular and extensible codebase\n\n"

    if doc_summary:
        readme += "## 📦 Modules & Functionality\n\n"
        readme += doc_summary + "\n\n"

    if os.path.exists("requirements.txt"):
        readme += "## 🛠 Installation\n\n"
        readme += "```bash\n"
        readme += "pip install -r requirements.txt\n"
        readme += "```\n\n"

    readme += "## 🚀 Usage\n\n"
    readme += "```bash\n"
    readme += "python main.py path/to/receipt_image.jpg\n"
    readme += "```\n\n"
    readme += "You can also modify configuration options inside `config.py` if present.\n\n"

    readme += "## 📁 Project Structure\n\n"
    readme += file_tree + "\n"

    if os.path.exists("LICENSE"):
        readme += "## 📝 License\n\n"
        readme += "This project is licensed under the terms of the [LICENSE](LICENSE) file.\n"

    # write file with UTF-8 encoding to support emojis/icons
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(readme)

    print("README.md generated for ReceiptRecon!")

if __name__ == "__main__":
    generate_readme()
