#!/usr/bin/env python3
"""Patch weston clients/window.c so CSD clients can publish content geometry."""

from __future__ import annotations

import sys
from pathlib import Path


def patch_window_get_geometry(text: str) -> str:
    old = """static void
window_get_geometry(struct window *window, struct rectangle *geometry)
{
	if (window->frame && !window->fullscreen)
		frame_input_rect(window->frame->frame,
				 &geometry->x,
				 &geometry->y,
				 &geometry->width,
				 &geometry->height);
	else
		window_get_allocation(window, geometry);
}"""
    new = """static void
window_get_geometry(struct window *window, struct rectangle *geometry)
{
	/*
	 * frame_input_rect() only excludes the drop shadow (shadow_margin),
	 * leaving the painted border + titlebar inside the reported xdg
	 * window geometry. window_sync_geometry() below runs on every
	 * redraw/commit and calls xdg_surface_set_window_geometry() with
	 * whatever this returns, so using frame_input_rect() here makes the
	 * compositor composite the client's border/titlebar chrome as if it
	 * were real content: the CSD border stays visible and cropping is
	 * off by the border width + titlebar height on every side.
	 * frame_interior() is the actual innermost content rect (border,
	 * titlebar, and shadow all excluded); use that so the compositor
	 * crops exactly the same region the client draws its content into.
	 */
	if (window->frame && !window->fullscreen)
		frame_interior(window->frame->frame,
				 &geometry->x,
				 &geometry->y,
				 &geometry->width,
				 &geometry->height);
	else if (window->fullscreen &&
		 window->last_geometry.width > 0 &&
		 window->last_geometry.height > 0 &&
		 (window->last_geometry.x > 0 ||
		  window->last_geometry.y > 0))
		*geometry = window->last_geometry;
	else
		window_get_allocation(window, geometry);
}"""
    if old not in text:
        raise SystemExit("window_get_geometry anchor missing in window.c")
    return text.replace(old, new, 1)


def patch_window_set_content_geometry(text: str) -> str:
    marker = "window_set_content_geometry(struct window *window"
    if marker in text:
        return text

    anchor = """static void
window_sync_geometry(struct window *window)
{"""
    insert = """void
window_set_content_geometry(struct window *window, int32_t x, int32_t y,
			    int32_t width, int32_t height)
{
	struct rectangle geometry;
	int32_t frame_x = 0, frame_y = 0;

	if (!window->xdg_surface || width <= 0 || height <= 0)
		return;

	/*
	 * x/y/width/height here are relative to the *child* widget's own
	 * content area (e.g. weston-terminal's cell-grid inset), not the
	 * decorated window buffer as a whole. xdg_surface_set_window_geometry()
	 * is defined in surface-local coordinates, i.e. relative to the top
	 * left of the CSD buffer that also contains the border/titlebar/drop
	 * shadow drawn by frame_repaint(). Without adding the frame's own
	 * interior offset here, the compositor crops only the caller's small
	 * child-relative inset and leaves the border/titlebar/shadow visible
	 * as part of the "content" it composites.
	 */
	if (window->frame)
		frame_interior(window->frame->frame, &frame_x, &frame_y,
				NULL, NULL);

	geometry.x = frame_x + x;
	geometry.y = frame_y + y;
	geometry.width = width;
	geometry.height = height;

	if (geometry.x == window->last_geometry.x &&
	    geometry.y == window->last_geometry.y &&
	    geometry.width == window->last_geometry.width &&
	    geometry.height == window->last_geometry.height)
		return;

	xdg_surface_set_window_geometry(window->xdg_surface,
					geometry.x, geometry.y,
					geometry.width, geometry.height);
	window->last_geometry = geometry;
}

"""
    if anchor not in text:
        raise SystemExit("window_sync_geometry anchor missing in window.c")
    return text.replace(anchor, insert + anchor, 1)


def patch_window_h(text: str) -> str:
    marker = "window_set_content_geometry"
    if marker in text:
        return text

    anchor = "void window_frame_set_child_size(struct widget *widget, int child_width,\n\t\t\t    int child_height);"
    if anchor not in text:
        anchor = "void\nwindow_frame_set_child_size(struct widget *widget, int child_width,\n\t\t\t    int child_height);"
    if anchor not in text:
        raise SystemExit("window_frame_set_child_size anchor missing in window.h")

    decl = (
        "\nvoid\n"
        "window_set_content_geometry(struct window *window, int32_t x, int32_t y,\n"
        "\t\t\t    int32_t width, int32_t height);\n"
    )
    return text.replace(anchor, anchor + decl, 1)


def main() -> None:
    if len(sys.argv) not in (2, 3):
        print(f"usage: {sys.argv[0]} <window.c> [window.h]", file=sys.stderr)
        sys.exit(2)

    window_c = Path(sys.argv[1])
    text = window_c.read_text()
    text = patch_window_set_content_geometry(text)
    text = patch_window_get_geometry(text)
    window_c.write_text(text)
    print(f"Patched {window_c}")

    if len(sys.argv) == 3:
        window_h = Path(sys.argv[2])
        window_h.write_text(patch_window_h(window_h.read_text()))
        print(f"Patched {window_h}")


if __name__ == "__main__":
    main()
