# Damage feedback

[Français](CONTRAST.md) · **English** · [Game](../README.md#english)

Pocket Depths uses a **brief software negative of the scene**, followed by two heart blinks when damage is taken. Health and ammunition digits remain readable. The physical contrast setting is unchanged.

The ALL RESET animation alternates characters and pixel patterns; it is not a software contrast control. See the [G805 firmware reference](../../../docs/ROM_G801_EN.md). G850 LCD contrast commands must not be applied to G801/G805 controllers.

To edit the effect, see `hurt_flash` in `depths.asm`, then `invert_buffer` and `.flash_wait` in `render.asm`. XOR mask 7Fh inverts the seven useful bits per column. No LCD port is accessed directly.
