try:
    with open("view_def.sql", "rb") as f:
        content = f.read()
    # Try utf-8 first, then utf-16
    try:
        print(content.decode("utf-8"))
    except:
        print(content.decode("utf-16"))
except Exception as e:
    print(f"Error: {e}")
