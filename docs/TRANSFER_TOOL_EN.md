# Sharp PC-G Link

[Français](TRANSFER_TOOL.md) · **English** · [Loading](LOADING_EN.md)

**Sharp PC-G Link** is the separate transfer utility. Download it from [its GitHub repository](https://github.com/pR-0000/Sharp-PC-G-Link), then follow its README. The [standalone Windows release](https://github.com/pR-0000/Sharp-PC-G-Link/releases/latest) starts with **Sharp PC-G Link.exe**, without Python. With Python 3.10+ and Tkinter, open **Sharp PC-G Link.pyw** in its root folder. It offers to install pyserial in a local environment if needed.

Alternative installation from the utility folder:

```text
python -m pip install -r requirements.txt
python -m sharp_link
```

Use **Send ASM** for the games' HEX/BIN files. [Loading instructions](LOADING_EN.md) give each game's USER reservation. BASIC examples are in `examples/basic/` of the utility repository. Language and serial settings are saved in its local INI file.
