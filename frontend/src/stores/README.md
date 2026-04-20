# Store Generation (Experimental)

Run the generator to create typed Zustand stores from backend Pydantic schemas:

```bash
cd backend
python -m app.scripts.generate_zustand_stores
```

Generated files are written to `frontend/src/stores/autogen/`.
