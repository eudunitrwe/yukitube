package main

import "fmt"

// The launcher's messages, in the language chosen in the YukiTube player
// (menu ⋮ → Language); English until one is chosen.
var messages = map[string]map[string]string{
	"firefox_missing": {
		"en": "Firefox is missing from %s.\n\nReinstall YukiTube (or extract the whole archive again).",
		"ro": "Firefox lipsește din %s.\n\nReinstalează YukiTube (sau dezarhivează din nou toată arhiva).",
		"ru": "Firefox отсутствует в %s.\n\nПереустановите YukiTube (или заново распакуйте весь архив).",
	},
	"not_writable": {
		"en": "YukiTube cannot write to %s.\n\nMove the YukiTube folder somewhere you can write to (for example Documents or a USB stick).\n\n%v",
		"ro": "YukiTube nu poate scrie în %s.\n\nMută folderul YukiTube într-un loc unde ai drept de scriere (de exemplu Documente sau un stick USB).\n\n%v",
		"ru": "YukiTube не может записывать в %s.\n\nПереместите папку YukiTube туда, где есть права на запись (например, в «Документы» или на флешку).\n\n%v",
	},
	"settings_copy": {
		"en": "The settings could not be copied: %v",
		"ro": "Setările nu au putut fi copiate: %v",
		"ru": "Не удалось скопировать настройки: %v",
	},
	"missing_file": {
		"en": "%s is missing: %v",
		"ro": "Lipsește %s: %v",
		"ru": "Отсутствует %s: %v",
	},
	"firefox_failed": {
		"en": "Firefox did not start: %v",
		"ro": "Firefox nu a pornit: %v",
		"ru": "Firefox не запустился: %v",
	},
	"remote_missing": {
		"en": "The YukiTube player is missing from %s.\n\nReinstall YukiTube (or extract the whole archive again).",
		"ro": "Telecomanda YukiTube lipsește din %s.\n\nReinstalează YukiTube (sau dezarhivează din nou toată arhiva).",
		"ru": "Плеер YukiTube отсутствует в %s.\n\nПереустановите YukiTube (или заново распакуйте весь архив).",
	},
	"remote_failed": {
		"en": "The YukiTube player did not start: %v",
		"ro": "Telecomanda YukiTube nu a pornit: %v",
		"ru": "Плеер YukiTube не запустился: %v",
	},
	"addons_list": {
		"en": "The add-on list is missing: %v",
		"ro": "Lipsește lista de extensii: %v",
		"ru": "Отсутствует список расширений: %v",
	},
	"addon_missing": {
		"en": "The %s add-on is missing: %v",
		"ro": "Lipsește extensia %s: %v",
		"ru": "Отсутствует расширение %s: %v",
	},
	"addon_corrupt": {
		"en": "The %s add-on is damaged (wrong checksum). Reinstall YukiTube.",
		"ro": "Extensia %s este coruptă (checksum greșit). Reinstalează YukiTube.",
		"ru": "Расширение %s повреждено (неверная контрольная сумма). Переустановите YukiTube.",
	},
	"addon_copy": {
		"en": "The %s add-on could not be copied: %v",
		"ro": "Extensia %s nu a putut fi copiată: %v",
		"ru": "Не удалось скопировать расширение %s: %v",
	},
}

func msg(key string, args ...any) error {
	m := messages[key]
	text, ok := m[uiLanguage()]
	if !ok {
		text = m["en"]
	}
	return fmt.Errorf(text, args...)
}
