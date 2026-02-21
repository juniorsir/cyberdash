import subprocess

class ShellCore:
    def execute(self, cmd: str):
        try:
            # Increased timeout to 300 seconds (5 minutes) for big tasks like 'pkg up'
            result = subprocess.run(
                cmd, 
                shell=True, 
                capture_output=True, 
                text=True, 
                timeout=300 
            )
            return result.stdout if result.stdout else result.stderr
        except subprocess.TimeoutExpired:
            return "Error: Command timed out. Task is too large for dashboard shell."
        except Exception as e:
            return f"Error: {str(e)}"
