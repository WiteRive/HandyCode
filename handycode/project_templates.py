"""
Шаблоны проектов для быстрой настройки
"""

from typing import Dict


TEMPLATES = {
    'python': {
        'description': 'Шаблон Python проекта',
        'files': {
            'src/__init__.py': '',
            'src/main.py': '"""Главный модуль"""\n\n\ndef main():\n    print("Привет, Мир!")\n\n\nif __name__ == "__main__":\n    main()\n',
            'tests/__init__.py': '',
            'tests/test_main.py': '"""Тесты"""\n\nfrom src.main import main\n\n\ndef test_main():\n    assert main() is None\n',
            'requirements.txt': '# Зависимости\n',
            'README.md': '# Проект\n\n## Установка\n\n```bash\npip install -r requirements.txt\n```\n\n## Запуск\n\n```bash\npython src/main.py\n```\n',
            '.gitignore': '__pycache__/\n*.pyc\n.env\nvenv/\ndist/\n',
        }
    },
    'react': {
        'description': 'React с Vite',
        'files': {
            'src/App.jsx': 'import React from "react";\n\nexport default function App() {\n  return <h1>Привет, Мир!</h1>;\n}\n',
            'src/main.jsx': 'import React from "react";\nimport ReactDOM from "react-dom/client";\nimport App from "./App";\n\nReactDOM.createRoot(document.getElementById("root")).render(\n  <React.StrictMode>\n    <App />\n  </React.StrictMode>\n);\n',
            'index.html': '<!DOCTYPE html>\n<html>\n<head>\n  <meta charset="UTF-8" />\n  <title>React App</title>\n</head>\n<body>\n  <div id="root"></div>\n  <script type="module" src="/src/main.jsx"></script>\n</body>\n</html>\n',
            'package.json': '{\n  "name": "react-app",\n  "version": "1.0.0",\n  "scripts": {\n    "dev": "vite",\n    "build": "vite build"\n  },\n  "dependencies": {\n    "react": "^18.2.0",\n    "react-dom": "^18.2.0"\n  },\n  "devDependencies": {\n    "@vitejs/plugin-react": "^4.0.0",\n    "vite": "^5.0.0"\n  }\n}\n',
            'vite.config.js': 'import { defineConfig } from "vite";\nimport react from "@vitejs/plugin-react";\n\nexport default defineConfig({\n  plugins: [react()]\n});\n',
            '.gitignore': 'node_modules/\ndist/\n',
        }
    },
    'fastapi': {
        'description': 'FastAPI проект',
        'files': {
            'app/__init__.py': '',
            'app/main.py': 'from fastapi import FastAPI\n\napp = FastAPI()\n\n\n@app.get("/")\nasync def root():\n    return {"message": "Привет, Мир!"}\n',
            'requirements.txt': 'fastapi\nuvicorn\n',
            'README.md': '# FastAPI Проект\n\n## Запуск\n\n```bash\nuvicorn app.main:app --reload\n```\n',
            '.gitignore': '__pycache__/\n*.pyc\n.env\nvenv/\n',
        }
    },
    'node': {
        'description': 'Node.js с Express',
        'files': {
            'src/index.js': 'const express = require("express");\n\nconst app = express();\nconst PORT = process.env.PORT || 3000;\n\napp.get("/", (req, res) => {\n  res.json({ message: "Привет, Мир!" });\n});\n\napp.listen(PORT, () => {\n  console.log(`Сервер: http://localhost:${PORT}`);\n});\n',
            'package.json': '{\n  "name": "node-app",\n  "version": "1.0.0",\n  "main": "src/index.js",\n  "scripts": {\n    "start": "node src/index.js"\n  },\n  "dependencies": {\n    "express": "^4.18.0"\n  }\n}\n',
            '.gitignore': 'node_modules/\n.env\n',
        }
    }
}


def get_template(template_name: str) -> Dict:
    """Получает шаблон проекта"""
    return TEMPLATES.get(template_name, {})