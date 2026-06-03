#include QMK_KEYBOARD_H
#include "version.h"
#define MOON_LED_LEVEL LED_LEVEL
#ifndef ZSA_SAFE_RANGE
#define ZSA_SAFE_RANGE SAFE_RANGE
#endif

enum custom_keycodes {
  RGB_SLD = ZSA_SAFE_RANGE,
};



#define DUAL_FUNC_0 LT(8, KC_7)
#define DUAL_FUNC_1 LT(9, KC_F9)
#define DUAL_FUNC_2 LT(2, KC_F6)
#define DUAL_FUNC_3 LT(1, KC_Z)
#define DUAL_FUNC_4 LT(9, KC_S)
#define DUAL_FUNC_5 LT(14, KC_F23)
#define DUAL_FUNC_6 LT(15, KC_D)
#define DUAL_FUNC_7 LT(5, KC_B)
#define DUAL_FUNC_8 LT(8, KC_B)

const uint16_t PROGMEM keymaps[][MATRIX_ROWS][MATRIX_COLS] = {
  [0] = LAYOUT_moonlander(
    KC_GRAVE,       KC_1,           KC_2,           KC_3,           KC_4,           KC_5,           KC_6,                                           DUAL_FUNC_5,    KC_LCBR,        KC_RCBR,        KC_LBRC,        KC_RBRC,        KC_MINUS,       KC_EQUAL,
    KC_TAB,         KC_Q,           KC_W,           KC_E,           KC_R,           KC_T,           KC_7,                                           KC_MS_WH_UP,    KC_Y,           KC_U,           KC_I,           KC_O,           KC_P,           KC_BSLS,
    MT(MOD_LCTL, KC_ESCAPE),KC_A,           KC_S,           KC_D,           KC_F,           KC_G,           KC_8,                                                                           KC_MS_WH_DOWN,  KC_H,           KC_J,           KC_K,           KC_L,           KC_SCLN,        KC_QUOTE,
    SC_LSPO,        KC_Z,           KC_X,           KC_C,           KC_V,           KC_B,                                           KC_N,           KC_M,           KC_COMMA,       KC_DOT,         KC_SLASH,       SC_RSPC,
    TT(2),          DUAL_FUNC_0,    DUAL_FUNC_1,    DUAL_FUNC_2,    DUAL_FUNC_3,    DUAL_FUNC_4,                                                                                                    LT(4, KC_ENTER),KC_LEFT,        KC_DOWN,        KC_UP,          KC_RIGHT,       TT(3),
    MT(MOD_LALT, KC_HOME),LT(3, KC_SPACE),MT(MOD_LCTL, KC_END),                MT(MOD_RCTL, KC_DELETE),LT(2, KC_SPACE),MT(MOD_RALT, KC_BSPC)
  ),
  [1] = LAYOUT_moonlander(
    KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT,                                 KC_PSCR,        KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT,
    KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT,                                 KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT,
    KC_ESCAPE,      KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT,                                                                 KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT,
    KC_LEFT_SHIFT,  KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT,                                 KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT, KC_RIGHT_SHIFT,
    TT(2),          DUAL_FUNC_6,    KC_9,           KC_0,           KC_ENTER,       MO(4),                                                                                                          LT(4, KC_ENTER),KC_LEFT,        KC_DOWN,        KC_UP,          KC_RIGHT,       TT(3),
    KC_LEFT_ALT,    KC_SPACE,       KC_LEFT_CTRL,                   KC_DELETE,      KC_SPACE,       KC_BSPC
  ),
  [2] = LAYOUT_moonlander(
    KC_NUM,         KC_F1,          KC_F2,          KC_F3,          KC_F4,          KC_F5,          KC_F6,                                          KC_TRANSPARENT, KC_NUM,         KC_KP_SLASH,    KC_KP_ASTERISK, KC_NO,          KC_SCRL,        KC_PAUSE,
    KC_KP_DOT,      KC_KP_ASTERISK, KC_KP_PLUS,     KC_KP_7,        KC_KP_8,        KC_KP_9,        KC_F7,                                          KC_TRANSPARENT, KC_KP_7,        KC_KP_8,        KC_KP_9,        KC_KP_MINUS,    KC_PAGE_UP,     KC_PGDN,
    KC_TRANSPARENT, KC_KP_SLASH,    KC_KP_MINUS,    KC_KP_4,        KC_KP_5,        KC_KP_6,        KC_F8,                                                                          KC_TRANSPARENT, KC_KP_4,        KC_KP_5,        KC_KP_6,        KC_KP_PLUS,     KC_HOME,        KC_END,
    DUAL_FUNC_7,    KC_F11,         KC_F12,         KC_KP_1,        KC_KP_2,        KC_KP_3,                                        KC_KP_1,        KC_KP_2,        KC_KP_3,        KC_KP_ENTER,    KC_TRANSPARENT, DUAL_FUNC_8,
    KC_TRANSPARENT, KC_INSERT,      KC_F9,          KC_F10,         KC_KP_0,        KC_KP_ENTER,                                                                                                    CW_TOGG,        KC_KP_0,        KC_KP_DOT,      KC_EQUAL,       KC_TRANSPARENT, TO(0),
    MT(MOD_LALT, KC_PAGE_UP),KC_SPACE,       MT(MOD_LCTL, KC_PGDN),                KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT
  ),
  [3] = LAYOUT_moonlander(
    TOGGLE_LAYER_COLOR,KC_TRANSPARENT, KC_MS_ACCEL0,   KC_MS_ACCEL1,   KC_MS_ACCEL2,   KC_TRANSPARENT, KC_TRANSPARENT,                                 KC_TRANSPARENT, KC_TRANSPARENT, KC_AUDIO_MUTE,  KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT, QK_BOOT,
    RGB_VAI,        KC_MS_BTN5,     KC_MS_WH_LEFT,  KC_MS_UP,       KC_MS_WH_RIGHT, KC_MS_WH_UP,    KC_TRANSPARENT,                                 KC_MS_WH_LEFT,  KC_TRANSPARENT, KC_AUDIO_VOL_DOWN,KC_AUDIO_VOL_UP,KC_TRANSPARENT, KC_MEDIA_PREV_TRACK,KC_MEDIA_NEXT_TRACK,
    RGB_VAD,        KC_MS_BTN4,     KC_MS_LEFT,     KC_MS_DOWN,     KC_MS_RIGHT,    KC_MS_WH_DOWN,  KC_TRANSPARENT,                                                                 KC_MS_WH_RIGHT, LCTL(LSFT(KC_LEFT)),LCTL(KC_LEFT),  LCTL(KC_RIGHT), LCTL(LSFT(KC_RIGHT)),KC_MEDIA_STOP,  KC_MEDIA_PLAY_PAUSE,
    MT(MOD_LSFT, KC_LBRC),KC_TRANSPARENT, KC_MS_BTN1,     KC_MS_BTN3,     KC_MS_BTN2,     KC_TRANSPARENT,                                 KC_TRANSPARENT, LCTL(LSFT(KC_T)),LCTL(KC_PAGE_UP),LCTL(KC_PGDN),  KC_TRANSPARENT, MT(MOD_RSFT, KC_RBRC),
    TO(0),          TO(1),          LGUI(LCTL(KC_LEFT)),LGUI(LCTL(KC_RIGHT)),KC_TRANSPARENT, AS_TOGG,                                                                                                        KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT,
    KC_TRANSPARENT, KC_TRANSPARENT, KC_TRANSPARENT,                 MT(MOD_RCTL, KC_INSERT),KC_SPACE,       KC_TRANSPARENT
  ),
  [4] = LAYOUT_moonlander(
    KC_INSERT,      KC_LCBR,        KC_RCBR,        KC_LBRC,        KC_RBRC,        KC_MINUS,       KC_EQUAL,                                       KC_GRAVE,       KC_1,           KC_2,           KC_3,           KC_4,           KC_5,           KC_6,
    KC_DELETE,      KC_Y,           KC_U,           KC_I,           KC_O,           KC_P,           KC_BSLS,                                        KC_TAB,         KC_Q,           KC_W,           KC_E,           KC_R,           KC_T,           KC_7,
    KC_BSPC,        KC_H,           KC_J,           KC_K,           KC_L,           KC_SCLN,        KC_QUOTE,                                                                       KC_ESCAPE,      KC_A,           KC_S,           KC_D,           KC_F,           KC_G,           KC_8,
    SC_RSPC,        KC_N,           KC_M,           KC_COMMA,       KC_DOT,         KC_SLASH,                                       KC_Z,           KC_X,           KC_C,           KC_V,           KC_B,           SC_LSPO,
    KC_ENTER,       KC_LEFT,        KC_DOWN,        KC_UP,          KC_RIGHT,       TO(0),                                                                                                          TO(0),          OSM(MOD_LGUI),  KC_9,           KC_0,           KC_HOME,        KC_END,
    OSM(MOD_LALT),  KC_SPACE,       OSM(MOD_LCTL),                  OSM(MOD_LCTL),  KC_SPACE,       OSM(MOD_LALT)
  ),
};





extern rgb_config_t rgb_matrix_config;

RGB hsv_to_rgb_with_value(HSV hsv) {
  RGB rgb = hsv_to_rgb( hsv );
  float f = (float)rgb_matrix_config.hsv.v / UINT8_MAX;
  return (RGB){ f * rgb.r, f * rgb.g, f * rgb.b };
}

void keyboard_post_init_user(void) {
  rgb_matrix_enable();
}

const uint8_t PROGMEM ledmap[][RGB_MATRIX_LED_COUNT][3] = {
    [0] = { {188,255,255}, {188,255,255}, {188,255,255}, {151,255,255}, {25,255,255}, {102,255,255}, {151,255,255}, {151,255,255}, {151,255,255}, {188,255,255}, {102,255,255}, {151,255,255}, {151,255,255}, {151,255,255}, {102,255,255}, {102,255,255}, {151,255,255}, {151,255,255}, {151,255,255}, {102,255,255}, {102,255,255}, {151,255,255}, {151,255,255}, {151,255,255}, {188,255,255}, {102,255,255}, {151,255,255}, {151,255,255}, {151,255,255}, {102,255,255}, {102,255,255}, {102,255,255}, {151,255,255}, {25,255,255}, {152,255,255}, {7,255,255}, {102,255,255}, {102,255,255}, {102,255,255}, {151,255,255}, {25,255,255}, {102,255,255}, {151,255,255}, {102,255,255}, {102,255,255}, {188,255,255}, {102,255,255}, {151,255,255}, {151,255,255}, {102,255,255}, {188,255,255}, {102,255,255}, {151,255,255}, {151,255,255}, {102,255,255}, {188,255,255}, {102,255,255}, {151,255,255}, {151,255,255}, {151,255,255}, {188,255,255}, {102,255,255}, {151,255,255}, {151,255,255}, {151,255,255}, {188,255,255}, {188,255,255}, {188,255,255}, {152,255,255}, {25,255,255}, {152,255,255}, {7,255,255} },

    [1] = { {188,255,255}, {188,255,255}, {188,255,255}, {188,255,255}, {0,245,245}, {102,255,255}, {151,255,255}, {25,255,255}, {151,255,255}, {25,255,255}, {102,255,255}, {25,255,255}, {25,255,255}, {151,255,255}, {102,255,255}, {102,255,255}, {151,255,255}, {25,255,255}, {151,255,255}, {102,255,255}, {102,255,255}, {151,255,255}, {151,255,255}, {151,255,255}, {25,255,255}, {102,255,255}, {151,255,255}, {151,255,255}, {151,255,255}, {102,255,255}, {102,255,255}, {102,255,255}, {151,255,255}, {25,255,255}, {151,255,255}, {0,245,245}, {102,255,255}, {102,255,255}, {102,255,255}, {151,255,255}, {0,245,245}, {102,255,255}, {151,255,255}, {102,255,255}, {102,255,255}, {25,255,255}, {102,255,255}, {151,255,255}, {151,255,255}, {102,255,255}, {25,255,255}, {102,255,255}, {151,255,255}, {151,255,255}, {102,255,255}, {25,255,255}, {102,255,255}, {151,255,255}, {151,255,255}, {151,255,255}, {25,255,255}, {102,255,255}, {151,255,255}, {151,255,255}, {151,255,255}, {188,255,255}, {188,255,255}, {188,255,255}, {151,255,255}, {25,255,255}, {151,255,255}, {25,255,255} },

    [2] = { {41,255,255}, {102,255,255}, {0,0,0}, {188,255,255}, {151,255,255}, {188,255,255}, {102,255,255}, {102,255,255}, {188,255,255}, {25,255,255}, {188,255,255}, {102,255,255}, {102,255,255}, {188,255,255}, {188,255,255}, {188,255,255}, {151,255,255}, {0,0,255}, {151,255,255}, {188,255,255}, {188,255,255}, {0,0,255}, {151,255,255}, {0,0,255}, {151,255,255}, {188,255,255}, {151,255,255}, {0,0,255}, {151,255,255}, {188,255,255}, {188,255,255}, {188,255,255}, {151,255,255}, {0,0,0}, {151,255,255}, {41,255,255}, {188,255,255}, {25,255,255}, {25,255,255}, {188,255,255}, {151,255,255}, {188,255,255}, {25,255,255}, {25,255,255}, {0,0,0}, {0,0,0}, {0,0,0}, {102,255,255}, {102,255,255}, {102,255,255}, {41,255,255}, {102,255,255}, {151,255,255}, {0,0,255}, {151,255,255}, {102,255,255}, {102,255,255}, {0,0,255}, {151,255,255}, {0,0,255}, {151,255,255}, {41,255,255}, {151,255,255}, {0,0,255}, {151,255,255}, {0,0,0}, {0,0,0}, {0,0,0}, {0,0,0}, {0,0,0}, {0,0,0}, {41,255,255} },

    [3] = { {0,0,0}, {0,0,0}, {0,0,0}, {0,0,0}, {151,255,255}, {0,0,0}, {25,255,255}, {25,255,255}, {0,0,0}, {25,255,255}, {0,245,245}, {188,255,255}, {74,255,255}, {25,255,255}, {188,255,255}, {0,245,245}, {74,255,255}, {74,255,255}, {25,255,255}, {188,255,255}, {0,245,245}, {188,255,255}, {74,255,255}, {25,255,255}, {0,0,0}, {0,0,0}, {188,255,255}, {188,255,255}, {0,0,0}, {0,0,0}, {0,0,0}, {0,0,0}, {0,0,0}, {0,0,0}, {0,0,0}, {41,255,255}, {41,255,255}, {0,245,245}, {0,245,245}, {0,0,0}, {152,255,255}, {0,0,0}, {0,245,245}, {255,245,245}, {0,0,0}, {0,0,0}, {0,0,0}, {0,0,0}, {151,255,255}, {25,255,255}, {0,0,0}, {0,0,0}, {41,255,255}, {74,255,255}, {25,255,255}, {0,0,0}, {41,255,255}, {41,255,255}, {74,255,255}, {25,255,255}, {0,0,0}, {0,0,0}, {0,0,0}, {151,255,255}, {0,0,0}, {0,0,0}, {188,255,255}, {188,255,255}, {0,0,0}, {0,0,0}, {151,255,255}, {0,0,0} },

    [4] = { {188,255,255}, {188,255,255}, {188,255,255}, {188,255,255}, {25,255,255}, {151,255,255}, {102,255,255}, {102,255,255}, {102,255,255}, {188,255,255}, {151,255,255}, {102,255,255}, {102,255,255}, {102,255,255}, {188,255,255}, {151,255,255}, {102,255,255}, {102,255,255}, {151,255,255}, {188,255,255}, {151,255,255}, {102,255,255}, {102,255,255}, {151,255,255}, {188,255,255}, {151,255,255}, {102,255,255}, {151,255,255}, {151,255,255}, {151,255,255}, {151,255,255}, {151,255,255}, {25,255,255}, {151,255,255}, {25,255,255}, {25,255,255}, {151,255,255}, {151,255,255}, {151,255,255}, {188,255,255}, {188,255,255}, {151,255,255}, {102,255,255}, {102,255,255}, {102,255,255}, {188,255,255}, {151,255,255}, {102,255,255}, {102,255,255}, {102,255,255}, {151,255,255}, {151,255,255}, {102,255,255}, {102,255,255}, {102,255,255}, {151,255,255}, {151,255,255}, {102,255,255}, {102,255,255}, {102,255,255}, {188,255,255}, {151,255,255}, {102,255,255}, {102,255,255}, {102,255,255}, {188,255,255}, {188,255,255}, {188,255,255}, {25,255,255}, {151,255,255}, {25,255,255}, {25,255,255} },

};

void set_layer_color(int layer) {
  for (int i = 0; i < RGB_MATRIX_LED_COUNT; i++) {
    HSV hsv = {
      .h = pgm_read_byte(&ledmap[layer][i][0]),
      .s = pgm_read_byte(&ledmap[layer][i][1]),
      .v = pgm_read_byte(&ledmap[layer][i][2]),
    };
    if (!hsv.h && !hsv.s && !hsv.v) {
        rgb_matrix_set_color( i, 0, 0, 0 );
    } else {
        RGB rgb = hsv_to_rgb_with_value(hsv);
        rgb_matrix_set_color(i, rgb.r, rgb.g, rgb.b);
    }
  }
}

bool rgb_matrix_indicators_user(void) {
  if (rawhid_state.rgb_control) {
      return false;
  }
  if (!keyboard_config.disable_layer_led) {
    switch (biton32(layer_state)) {
      case 0:
        set_layer_color(0);
        break;
      case 1:
        set_layer_color(1);
        break;
      case 2:
        set_layer_color(2);
        break;
      case 3:
        set_layer_color(3);
        break;
      case 4:
        set_layer_color(4);
        break;
     default:
        if (rgb_matrix_get_flags() == LED_FLAG_NONE) {
          rgb_matrix_set_color_all(0, 0, 0);
        }
    }
  } else {
    if (rgb_matrix_get_flags() == LED_FLAG_NONE) {
      rgb_matrix_set_color_all(0, 0, 0);
    }
  }

  return true;
}




bool process_record_user(uint16_t keycode, keyrecord_t *record) {
  switch (keycode) {
  case QK_MODS ... QK_MODS_MAX:
    // Mouse and consumer keys (volume, media) with modifiers work inconsistently across operating systems,
    // this makes sure that modifiers are always applied to the key that was pressed.
    if (IS_MOUSE_KEYCODE(QK_MODS_GET_BASIC_KEYCODE(keycode)) || IS_CONSUMER_KEYCODE(QK_MODS_GET_BASIC_KEYCODE(keycode))) {
      if (record->event.pressed) {
        add_mods(QK_MODS_GET_MODS(keycode));
        send_keyboard_report();
        wait_ms(2);
        register_code(QK_MODS_GET_BASIC_KEYCODE(keycode));
        return false;
      } else {
        wait_ms(2);
        del_mods(QK_MODS_GET_MODS(keycode));
      }
    }
    break;

    case DUAL_FUNC_0:
      if (record->tap.count > 0) {
        if (record->event.pressed) {
          register_code16(LCTL(KC_GRAVE));
        } else {
          unregister_code16(LCTL(KC_GRAVE));
        }
      } else {
        if (record->event.pressed) {
          register_code16(LCTL(KC_V));
        } else {
          unregister_code16(LCTL(KC_V));
        }
      }
      return false;
    case DUAL_FUNC_1:
      if (record->tap.count > 0) {
        if (record->event.pressed) {
          register_code16(KC_9);
        } else {
          unregister_code16(KC_9);
        }
      } else {
        if (record->event.pressed) {
          register_code16(LCTL(KC_X));
        } else {
          unregister_code16(LCTL(KC_X));
        }
      }
      return false;
    case DUAL_FUNC_2:
      if (record->tap.count > 0) {
        if (record->event.pressed) {
          register_code16(KC_0);
        } else {
          unregister_code16(KC_0);
        }
      } else {
        if (record->event.pressed) {
          register_code16(LCTL(KC_C));
        } else {
          unregister_code16(LCTL(KC_C));
        }
      }
      return false;
    case DUAL_FUNC_3:
      if (record->tap.count > 0) {
        if (record->event.pressed) {
          register_code16(LALT(KC_SPACE));
        } else {
          unregister_code16(LALT(KC_SPACE));
        }
      } else {
        if (record->event.pressed) {
          register_code16(KC_LEFT_GUI);
        } else {
          unregister_code16(KC_LEFT_GUI);
        }
      }
      return false;
    case DUAL_FUNC_4:
      if (record->tap.count > 0) {
        if (record->event.pressed) {
          register_code16(LGUI(KC_2));
        } else {
          unregister_code16(LGUI(KC_2));
        }
      } else {
        if (record->event.pressed) {
          layer_on(4);
        } else {
          layer_off(4);
        }
      }
      return false;
    case DUAL_FUNC_5:
      if (record->tap.count > 0) {
        if (record->event.pressed) {
          register_code16(KC_PSCR);
        } else {
          unregister_code16(KC_PSCR);
        }
      } else {
        if (record->event.pressed) {
          register_code16(LGUI(LSFT(KC_S)));
        } else {
          unregister_code16(LGUI(LSFT(KC_S)));
        }
      }
      return false;
    case DUAL_FUNC_6:
      if (record->tap.count > 0) {
        if (record->event.pressed) {
          layer_move(0);
        } else {
          layer_move(0);
        }
      } else {
        if (record->event.pressed) {
          layer_on(4);
        } else {
          layer_off(4);
        }
      }
      return false;
    case DUAL_FUNC_7:
      if (record->tap.count > 0) {
        if (record->event.pressed) {
          register_code16(KC_LCBR);
        } else {
          unregister_code16(KC_LCBR);
        }
      } else {
        if (record->event.pressed) {
          register_code16(KC_LEFT_SHIFT);
        } else {
          unregister_code16(KC_LEFT_SHIFT);
        }
      }
      return false;
    case DUAL_FUNC_8:
      if (record->tap.count > 0) {
        if (record->event.pressed) {
          register_code16(KC_RCBR);
        } else {
          unregister_code16(KC_RCBR);
        }
      } else {
        if (record->event.pressed) {
          register_code16(KC_RIGHT_SHIFT);
        } else {
          unregister_code16(KC_RIGHT_SHIFT);
        }
      }
      return false;
    case RGB_SLD:
        if (rawhid_state.rgb_control) {
            return false;
        }
        if (record->event.pressed) {
            rgblight_mode(1);
        }
        return false;
  }
  return true;
}
