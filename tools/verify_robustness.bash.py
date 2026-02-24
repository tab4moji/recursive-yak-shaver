import sys
import os
import json

# RYS のパスを追加
sys.path.append(os.path.abspath("./rys"))
from phase_utils import invoke_coder

def test_factorization_syntax():
    script_dir = os.path.abspath("./rys")
    llm_config = {
        "host": os.environ.get("RYS_LLM_HOST", "http://localhost"),
        "port": os.environ.get("RYS_LLM_PORT", "11434"),
        "model": os.environ.get("RYS_LLM_MODEL", "gemma3n:e4b")
    }
    
    # テスト対象のタスク定義
    task = {
        "id": "Task1",
        "title": "Prime factorization",
        "skill": "python_math",
        "input": {
            "type": "value",
            "value": {
                "type": "value",
                "value": "234314121"
            }
        }
    }
    
    prompt = "Skill: python_math\nTask: " + task['title'] + "\nInput: " + json.dumps(task['input']) + "\n"
    
    print("Testing LLM Code Generation (Single Call)...")
    # invoke_coder を呼び出し（新ロジックによりチートシートが優先されるはず）
    snippet = invoke_coder(script_dir, prompt, "python_math", llm_config, task=task)
    
    print("--- Generated Snippet ---")
    print(snippet)
    print("-------------------------")
    
    # 構文チェック
    try:
        compile(snippet, '<string>', 'exec')
        print("\nSUCCESS: No SyntaxError found.")
    except SyntaxError as e:
        print(f"\nFAILURE: SyntaxError: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_factorization_syntax()
