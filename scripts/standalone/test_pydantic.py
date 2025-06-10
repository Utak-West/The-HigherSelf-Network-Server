"""
Test file to check if Pydantic is working correctly.
"""

try:
    from pydantic import BaseModel
    
    class TestModel(BaseModel):
        name: str
        age: int
        
    model = TestModel(name="Test", age=30)
    print("Pydantic is working correctly!")
    print(f"Model: {model}")
except Exception as e:
    print(f"Error importing or using Pydantic: {e}")
