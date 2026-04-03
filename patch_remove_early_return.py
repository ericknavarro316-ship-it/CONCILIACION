with open('app.py', 'r') as f:
    content = f.read()

search = """                            except Exception as e:
                                pass

                        if not uuid_str:
                            return None

                        # Determinar ruta destino"""

replace = """                            except Exception as e:
                                pass

                        # Determinar ruta destino"""

content = content.replace(search, replace)

with open('app.py', 'w') as f:
    f.write(content)
