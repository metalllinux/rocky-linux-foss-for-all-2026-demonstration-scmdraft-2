/**
 * rdp-shot: capture the gnome-remote-desktop RDP session framebuffer on the
 * controller side, and optionally inject keyboard/pointer events in the same
 * connection before capturing. This is the TASK-0042 screenshot fallback that
 * touches the target not at all: it reads the surface the RDP server already
 * composites, so it does not depend on the org.gnome.Shell.Screenshot D-Bus API
 * that this target now denies. Built on FreeRDP 3 (Apache-2.0), same transport
 * as rdp-input.c (same team, same license).
 *
 * Usage: rdp-shot <argsfile> <out.ppm> [<event> ...]
 *   <argsfile>  xfreerdp-style arguments, one per line (/v:/u:/p:/cert:ignore/w:/h:)
 *   <out.ppm>   P6 PPM file written from the decoded primary surface
 *   events (played after connect, before capture):
 *     move <x> <y> | click <x> <y> | key <scancode> | keyx <scancode>
 *     keydown <scancode> | keyup <scancode> | type <text> | wait <ms>
 *
 * License: Apache-2.0 (links libfreerdp3 / libfreerdp-client3, Apache-2.0).
 * Build: gcc -w -o rdp-shot rdp-shot.c $(pkg-config --cflags --libs freerdp3 freerdp-client3)
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include <freerdp/freerdp.h>
#include <freerdp/input.h>
#include <freerdp/settings.h>
#include <freerdp/error.h>
#include <freerdp/client.h>
#include <freerdp/client/cmdline.h>
#include <freerdp/client/channels.h>
#include <freerdp/client/rdpgfx.h>
#include <freerdp/client/video.h>
#include <freerdp/client/geometry.h>
#include <freerdp/gdi/gdi.h>
#include <freerdp/gdi/gfx.h>
#include <freerdp/gdi/video.h>
#include <freerdp/codec/color.h>

#include <winpr/wtypes.h>

#define MAX_ARGS 32
#define MAX_LINE 512
/* GDI destination format: 4 bytes/pixel, memory order B,G,R,X. */
#define CAP_FORMAT PIXEL_FORMAT_BGRX32
#define BYTES_PER_PIXEL 4

static int my_client_new(freerdp *instance, rdpContext *context)
{
	(void)instance; (void)context;
	return 1;
}

static void my_client_free(freerdp *instance, rdpContext *context)
{
	(void)instance; (void)context;
}

/* GDI is initialised in PostConnect, not PreConnect: at PostConnect the
 * negotiated surface size and the update/codec contexts already exist, which is
 * what gdi_init_ex needs. Preserve whatever PostConnect the client library set. */
static pConnectCallback g_orig_post_connect = NULL;

static BOOL my_post_connect(freerdp *instance)
{
	if (g_orig_post_connect && !g_orig_post_connect(instance))
		return FALSE;
	rdpGdi *gdi = instance->context->gdi;
	if (gdi == NULL) {
		if (!gdi_init(instance, CAP_FORMAT)) {
			fprintf(stderr, "error: gdi_init failed in PostConnect\n");
			return FALSE;
		}
	}
	printf("stage3: gdi ready (gdi=%p)\n", (void *)instance->context->gdi);
	return TRUE;
}

static int parse_args_file(const char *path, char **argv, int max_args)
{
	FILE *f = fopen(path, "r");
	if (!f) {
		fprintf(stderr, "error: cannot open args file: %s\n", path);
		return -1;
	}
	int count = 0;
	argv[count++] = "rdp-shot";
	char line[MAX_LINE];
	while (fgets(line, sizeof(line), f) && count < max_args) {
		size_t len = strlen(line);
		while (len > 0 && (line[len - 1] == '\n' || line[len - 1] == '\r'))
			line[--len] = '\0';
		if (len == 0) continue;
		argv[count] = strdup(line);
		if (!argv[count]) { fclose(f); return -1; }
		count++;
	}
	fclose(f);
	return count;
}

static unsigned int next_utf8(const char **p)
{
	const unsigned char *s = (const unsigned char *)*p;
	if (!*s) return 0;
	unsigned int cp, extra;
	if (s[0] < 0x80) { cp = s[0]; extra = 0; }
	else if ((s[0] & 0xE0) == 0xC0) { cp = s[0] & 0x1F; extra = 1; }
	else if ((s[0] & 0xF0) == 0xE0) { cp = s[0] & 0x0F; extra = 2; }
	else if ((s[0] & 0xF8) == 0xF0) { cp = s[0] & 0x07; extra = 3; }
	else { *p += 1; return 0; }
	for (unsigned int i = 0; i < extra; i++) {
		if ((s[1 + i] & 0xC0) != 0x80) { *p += 1; return 0; }
		cp = (cp << 6) | (s[1 + i] & 0x3F);
	}
	*p += 1 + extra;
	return cp;
}

static BOOL send_type(rdpInput *input, const char *text)
{
	const char *p = text;
	unsigned int cp;
	while ((cp = next_utf8(&p)) != 0) {
		if (cp > 0xFFFF) return FALSE;
		if (!freerdp_input_send_unicode_keyboard_event(input, 0, (UINT16)cp)) return FALSE;
		usleep(20000);
		if (!freerdp_input_send_unicode_keyboard_event(input, KBD_FLAGS_RELEASE, (UINT16)cp)) return FALSE;
		usleep(20000);
	}
	return TRUE;
}

static BOOL send_key(rdpInput *input, const char *sc, BOOL extended)
{
	UINT8 code = (UINT8)strtoul(sc, NULL, 0);
	UINT16 down = KBD_FLAGS_DOWN | (extended ? KBD_FLAGS_EXTENDED : 0);
	UINT16 up = KBD_FLAGS_RELEASE | (extended ? KBD_FLAGS_EXTENDED : 0);
	if (!freerdp_input_send_keyboard_event(input, down, code)) return FALSE;
	usleep(40000);
	if (!freerdp_input_send_keyboard_event(input, up, code)) return FALSE;
	return TRUE;
}

static BOOL send_keydown(rdpInput *input, const char *sc)
{
	UINT8 code = (UINT8)strtoul(sc, NULL, 0);
	return freerdp_input_send_keyboard_event(input, KBD_FLAGS_DOWN, code);
}

static BOOL send_keyup(rdpInput *input, const char *sc)
{
	UINT8 code = (UINT8)strtoul(sc, NULL, 0);
	return freerdp_input_send_keyboard_event(input, KBD_FLAGS_RELEASE, code);
}

static BOOL send_click(rdpInput *input, UINT16 x, UINT16 y)
{
	if (!freerdp_input_send_mouse_event(input, PTR_FLAGS_MOVE, x, y)) return FALSE;
	usleep(80000);
	if (!freerdp_input_send_mouse_event(input, PTR_FLAGS_DOWN | PTR_FLAGS_BUTTON1, x, y)) return FALSE;
	usleep(80000);
	if (!freerdp_input_send_mouse_event(input, PTR_FLAGS_BUTTON1, x, y)) return FALSE;
	return TRUE;
}

/* Write the decoded GDI primary surface as a binary PPM (P6, RGB). */
static BOOL g_pipeline_wired = FALSE;

/* The rdpgfx addin creates gdi->gfx lazily when its dynamic channel opens, after
 * PostConnect. Poll and bind the GDI pipeline as soon as that context exists, so
 * the CAPROGRESSIVE/AVC frames decode into gdi->primary_buffer. */
static void try_wire_pipeline(freerdp *instance)
{
	if (g_pipeline_wired) return;
	rdpGdi *gdi = instance->context->gdi;
	if (gdi && gdi->gfx) {
		if (gdi_graphics_pipeline_init(gdi, gdi->gfx)) {
			g_pipeline_wired = TRUE;
			printf("stage4: gfx pipeline bound to gdi (gfx=%p)\n", (void *)gdi->gfx);
		}
	}
}

static int dump_surface_ppm(freerdp *instance, const char *path)
{
	rdpGdi *gdi = instance->context->gdi;
	if (!gdi || !gdi->primary_buffer) {
		fprintf(stderr, "error: no decoded surface (gdi=%p buf=%p)\n",
		        (void *)gdi, gdi ? (void *)gdi->primary_buffer : NULL);
		return -1;
	}
	/* Last-chance pipeline bind: the gfx context may only surface late. */
	fprintf(stdout, "probe: gdi->gfx=%p pipeline_wired=%d\n", (void *)gdi->gfx, g_pipeline_wired);
	if (!g_pipeline_wired && gdi->gfx) {
		if (gdi_graphics_pipeline_init(gdi, gdi->gfx))
			g_pipeline_wired = TRUE;
	}
	int w = gdi->width, h = gdi->height;
	if (w <= 0 || h <= 0) { fprintf(stderr, "error: bad surface dims %dx%d\n", w, h); return -1; }
	/* The primary surface buffer is contiguous: prefer a non-zero stride from the
	 * GDI, otherwise fall back to width * bytes-per-pixel. */
	size_t stride = gdi->bitmap_stride ? gdi->bitmap_stride : (size_t)gdi->stride;
	if (stride < (size_t)w * BYTES_PER_PIXEL)
		stride = (size_t)w * BYTES_PER_PIXEL;
	fprintf(stdout, "surface: gdi->stride=%u bitmap_stride=%u effective=%zu\n",
	        gdi->stride, gdi->bitmap_stride, stride);

	FILE *f = fopen(path, "wb");
	if (!f) { fprintf(stderr, "error: cannot open %s for writing\n", path); return -1; }
	fprintf(f, "P6\n%d %d\n255\n", w, h);
	for (int y = 0; y < h; y++) {
		const BYTE *row = gdi->primary_buffer + (size_t)y * stride;
		for (int x = 0; x < w; x++) {
			const BYTE *px = row + (size_t)x * BYTES_PER_PIXEL; /* B,G,R,X */
			BYTE rgb[3] = { px[2], px[1], px[0] };
			fwrite(rgb, 1, 3, f);
		}
	}
	fclose(f);
	fprintf(stdout, "captured %dx%d stride=%zu -> %s\n", w, h, stride, path);
	return 0;
}

int main(int argc, char *argv[])
{
	if (argc < 3) {
		fprintf(stderr,
			"usage: rdp-shot <argsfile> <out.ppm> [events...]\n"
			"  events: key sc | keyx sc | keydown sc | keyup sc | type text\n"
			"          | move x y | click x y | wait ms\n");
		return 1;
	}
	setvbuf(stdout, NULL, _IONBF, 0);
	const char *argsfile = argv[1];
	const char *outpath = argv[2];

	char *cmdline[MAX_ARGS];
	int cmdline_argc = parse_args_file(argsfile, cmdline, MAX_ARGS);
	if (cmdline_argc < 2) {
		fprintf(stderr, "error: args file has no arguments\n");
		return 1;
	}
	/* Number of strdup() heap args (indices 1..heap_args). Injected literals are
	 * static and must never be free()'d. */
	int heap_args = cmdline_argc - 1;
	/* Inject diagnostics without editing the credential args file. */
	if (cmdline_argc + 1 < MAX_ARGS) {
		cmdline[cmdline_argc++] = (char *)"/gfx:RFX9";
	}

	rdpSettings *settings = freerdp_settings_new(0);
	if (!settings) { fprintf(stderr, "error: freerdp_settings_new failed\n"); return 1; }

	int rc = freerdp_client_settings_parse_command_line_arguments(settings, cmdline_argc, cmdline, FALSE);
	if (rc < 0) {
		fprintf(stderr, "error: failed to parse args (rc=%d)\n", rc);
		for (int i = 1; i <= heap_args; i++) free(cmdline[i]);
		freerdp_settings_free(settings);
		return 1;
	}
	freerdp_settings_set_bool(settings, FreeRDP_SupportDynamicChannels, TRUE);

	RDP_CLIENT_ENTRY_POINTS entry = {0};
	entry.Size = sizeof(entry);
	entry.Version = RDP_CLIENT_INTERFACE_VERSION;
	entry.settings = settings;
	entry.ContextSize = sizeof(rdpClientContext);
	entry.ClientNew = my_client_new;
	entry.ClientFree = my_client_free;

	rdpContext *context = freerdp_client_context_new(&entry);
	if (!context) {
		fprintf(stderr, "error: freerdp_client_context_new failed\n");
		for (int i = 1; i <= heap_args; i++) free(cmdline[i]);
		freerdp_settings_free(settings);
		return 1;
	}
	freerdp *instance = context->instance;
	printf("stage1: context_new ok, instance=%p\n", (void *)instance);

	/* Wrap whatever PostConnect the client library installed. */
	g_orig_post_connect = instance->PostConnect;
	instance->PostConnect = my_post_connect;
	printf("stage2: postconnect wrapped (orig=%p)\n", (void *)g_orig_post_connect);

	printf("connecting (args from %s) ...\n", argsfile);
	if (!freerdp_connect(instance)) {
		UINT32 err = freerdp_get_last_error(context);
		fprintf(stderr, "error: connect failed (%s): %s\n",
		        freerdp_get_last_error_name(err) ? freerdp_get_last_error_name(err) : "unknown",
		        freerdp_get_last_error_string(err) ? freerdp_get_last_error_string(err) : "no detail");
		for (int i = 1; i <= heap_args; i++) free(cmdline[i]);
		freerdp_client_context_free(context);
		return 1;
	}

	rdpInput *input = context->input;
	usleep(700000); /* let the session activate and the first full frame arrive */

	int failed = 0;
	for (int i = 3; i < argc && !failed; i++) {
		const char *ev = argv[i];
		if (strcmp(ev, "key") == 0 && i + 1 < argc) failed = !send_key(input, argv[++i], FALSE);
		else if (strcmp(ev, "keyx") == 0 && i + 1 < argc) failed = !send_key(input, argv[++i], TRUE);
		else if (strcmp(ev, "keydown") == 0 && i + 1 < argc) failed = !send_keydown(input, argv[++i]);
		else if (strcmp(ev, "keyup") == 0 && i + 1 < argc) failed = !send_keyup(input, argv[++i]);
		else if (strcmp(ev, "type") == 0 && i + 1 < argc) failed = !send_type(input, argv[++i]);
		else if (strcmp(ev, "click") == 0 && i + 2 < argc) {
			UINT16 x = (UINT16)atoi(argv[++i]); UINT16 y = (UINT16)atoi(argv[++i]);
			failed = !send_click(input, x, y);
		} else if (strcmp(ev, "move") == 0 && i + 2 < argc) {
			UINT16 x = (UINT16)atoi(argv[++i]); UINT16 y = (UINT16)atoi(argv[++i]);
			failed = !freerdp_input_send_mouse_event(input, PTR_FLAGS_MOVE, x, y);
		} else if (strcmp(ev, "wait") == 0 && i + 1 < argc) {
			int ms = atoi(argv[++i]);
			printf("event: wait %d ms (pumping updates)\n", ms);
			/* Pump the event queue so incoming gfx frames are decoded into the
			 * surface while we wait, instead of sleeping through them. */
			int pumped = 0;
			while (pumped < ms) {
				if (!freerdp_check_event_handles(context)) {
					fprintf(stderr, "error: event handles failed during wait\n");
					failed = 1;
					break;
				}
				try_wire_pipeline(instance);
				usleep(50000);
				pumped += 50;
			}
		} else { fprintf(stderr, "error: unknown/incomplete event: %s\n", ev); failed = 1; }
	}

	/* Drain pending PDU/update messages so the surface is as complete as possible. */
	for (int i = 0; i < 20 && !failed; i++) {
		if (!freerdp_check_event_handles(context)) {
			fprintf(stderr, "error: event handles failed\n");
			failed = 1;
			break;
		}
		try_wire_pipeline(instance);
		usleep(50000);
	}

	int dump_rc = dump_surface_ppm(instance, outpath);

	freerdp_disconnect(instance);
	for (int i = 1; i <= heap_args; i++) free(cmdline[i]);
	freerdp_client_context_free(context);
	printf("done%s.\n", (failed || dump_rc) ? " WITH ERRORS" : "");
	return (failed || dump_rc) ? 1 : 0;
}
