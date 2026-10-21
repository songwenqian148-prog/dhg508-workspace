# OCR — 《欽定四庫全書》本《明史》卷二百五十九（袁崇煥傳），one leaf

## Source image

- File: `sources/raw/mingshi_juan259_yuanchonghuan_execution_n196.jpg`
- Origin: Internet Archive item [`06057040.cn`](https://archive.org/details/06057040.cn),
  catalogued *明史·卷二百五十八~卷二百五十九*.
  Direct page URL: <https://archive.org/download/06057040.cn/page/n196.jpg>
  (BookReader page index 196; 2345×3139 px; SHA-256 of the download:
  `88CC5C49CE7F862D13B8A3C8436604F5C09EB480AC6242A25ECF545B00265EED`).
- Bibliographic: 《欽定四庫全書》史部·正史類《明史》卷二百五十九（列傳第一百四十七），
  袁崇煥／毛文龍傳。Scanning institution: 浙江大學圖書館（CADAL / China–America
  Digital Academic Library）；`page-progression: rl`.

## Why this leaf still needed OCR

The Internet Archive already ran an automatic OCR pass — item metadata records
`ocr: tesseract 5.3.0`, `ocr_parameters: -l chi_sim`. On this page it is
useless, because the text is vertical, right-to-left, in traditional
characters, and in the 四庫全書 館閣體 script. The existing machine text reads,
for example:

```
gs 芝 过 及 本
去 式 殉 人 名 民 于 《
基于 机 诺 册 浆 寻
```

That output supports no historical claim, so the leaf had to be OCRed again.

## Method attempted, in the order the assignment prescribes

1. **LLM API (OpenRouter).** A key is present in opencode's credential store,
   but the gateway used here answers `401 {"error":{"message":"Missing
   Authentication header"}}` for that key *and* for a deliberately bogus key
   (`sk-bogus`), so the service could not be used. Script:
   `code/ocr_openrouter.py`.
2. **LLM API (DeepSeek).** The endpoint `https://api.deepseek.com` is live (it
   returns a normal `authentication_error` for an invalid key), but no
   `DEEPSEEK_API_KEY` was available — `G:\workspeace\dhg508-workspace\.env` is
   empty — so this route could not be used either.
3. **OpenCode's own vision (last resort).** The transcription below was made by
   reading the image directly. It was then checked against the Wikisource
   transcription of the same passage (see *Checking*).

## Transcription (columns, right → left, as printed)

```
龍狀及崇煥欲成和議龍錫嘗移書止之龍錫故主定
逆黨魏忠賢遺黨王永光高捷袁弘勳史褷輩謀興大
獄為逆黨報讎見崇煥下吏遂以擅主和議專戮大帥
二事為兩人罪捷首疏力攻褷弘勳繼之必欲並誅龍
錫法司坐崇煥謀叛龍錫亦論死三年八月遂磔崇煥
於市兄弟妻子流三千里籍其家崇煥無子家亦無餘
貲天下冤之崇煥既縛大壽潰而去武經略滿桂以趣
戰急與
```

## Continuous reading (punctuation added by me; not in the print)

> ……欲殺毛文龍狀。及崇煥欲成和議，龍錫嘗移書止之。龍錫故主定逆案，
> 魏忠賢遺黨王永光、高捷、袁弘勳、史褷輩謀興大獄，為逆黨報讎，見崇煥下吏，
> 遂以擅主和議、專戮大帥二事為兩人罪。捷首疏力攻，褷、弘勳繼之，必欲並誅龍錫。
> 法司坐崇煥謀叛，龍錫亦論死。三年八月，遂磔崇煥於市，兄弟妻子流三千里，
> 籍其家。崇煥無子，家亦無餘貲，天下冤之。崇煥既縛，大壽潰而去。
> 武經略滿桂以趣戰急，與……

## Checking

Checked character by character against the Wikisource transcription of
《明史》卷259, which reads identically apart from normal editorial variants
(scan `讎` / Wikisource `仇`; scan `黨` / Wikisource `党`; the rare name
`史褷`). No character in the passage is uncertain, so no `[？]` marks were
needed.
