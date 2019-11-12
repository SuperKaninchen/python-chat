/**
 * chatwatch - listen to Superkaninchen's python-chat
 * FWB 11/2019
 */

/**
 * UseDynDns: If this is true then use DynDNS,
 * otherwise use ServConf and read IP of
 * chat server from file on SD card.
 * If you set UseDynDns to true then you must
 * also specify the DynDnsServer and the
 * ChatServer.
 */
bool UseDynDns = true;

/**
 * This needs to be specified only if you set
 * UseDynDns to true. It must contain the IP
 * address of the DynDNS server to ask for
 * ChatServer's IP address.
 */
char DynDnsServer[] = "81.89.239.232";

/**
 * This needs to be specified only if you set
 * UseDynDns to true. It must contain the
 * name of the chat server.
 */
char ChatServer[] = "chat.tdyn.de";

/**
 * The port of the chat server.
 */
uint16_t ChatPort = 5000;

/**
 * This needs to be specified only if you set
 * UseDynDns to false. 
 * It contains IP# of the chat server.
 */
#define ServConf "CHATSERV.TXT"

/**
 * WiFi configuration file, it contains up to
 * MAX_SSID WiFi configurations.
 * Each configuration consists of one line
 * with the SSID and one line with the PSK.
 */
#define WifiConf "CHATWIFI.TXT"

#define MAX_SSID 4
char *WifiSsid;
char *WifiPsk;
#define SSID_MAX_SIZE 22
#define PSK_MAX_SIZE 30
char WifiSsidList[MAX_SSID+1][SSID_MAX_SIZE+1];
char WifiPskList[MAX_SSID+1][PSK_MAX_SIZE+1];


#include <stdlib.h>
#include <string.h>
#include <HTTPClient.h>
#include <SD.h>
#include <FS.h>

// Graphics and font library
#include <TFT_eSPI.h>
#include <SPI.h>
TFT_eSPI tft = TFT_eSPI();  // Invoke library
//#include <TFTShape.h>   // if you want do render results as graphics
#include <lwip/dns.h>
#include <lwip/ip_addr.h>
#include <esp32-hal-ledc.h>

#define LOGO_FILE "/chatwatch.ppm"

#define FONT_SMALL "Chicago20"
#define FONT "Chicago22"

#define PIN_BLUE_LED  2
#define TONE_PIN_CHANNEL 0
#define SPEAKER_PIN 26
// from utility/Config.h:
#define TFT_DC 21
#define TFT_CS 5
#define TFT_LED_PIN 14
#define TFT_MOSI 23
#define TFT_MISO 19
#define TFT_SCLK 18
#define TFT_RST -1

#define PPM_HEADER_SIZE 512
#define BUFSIZE 32768
uint8_t rgbBuf[BUFSIZE+1];
int rgbCursor;
#define MAX_THREAD_SIZE 14
#define STRING_SIZE 24
#define SERV_MAX_SIZE 40
char Server[SERV_MAX_SIZE+1];
char ServerIP[STRING_SIZE+1];
WiFiClient client;
bool connected = false;
uint8_t connectBuf[BUFSIZE+1];

static const char ERROR[] = "ERROR";

static void halt(String message) {
    Serial.println(message);
    digitalWrite(PIN_BLUE_LED, LOW);
    while(1) yield();
}

static void flashLed() {
  digitalWrite(PIN_BLUE_LED, LOW);
  delay(50);
  digitalWrite(PIN_BLUE_LED, HIGH);
}

static void checkSpiffs() {
  if (!SPIFFS.begin()) {
    halt("SPIFFS initialisation failed!");
  }
  // ESP32 will crash if any of the fonts are missing
  bool font_missing = false;
  if (SPIFFS.exists("/" FONT ".vlw") == false) font_missing = true;
  if (SPIFFS.exists("/" FONT_SMALL ".vlw") == false) font_missing = true;
  if (font_missing)
  {
    halt("Fonts missing in SPIFFS, did you upload it?");
  }
  if (SPIFFS.exists(LOGO_FILE) == false) halt("Logo file missing.");
}

static void initializeSD() {
  // Initialise the SD library before the TFT so the chip select is defined
  if (!SD.begin()) {
    halt("Card Mount Failed");
  }
  uint8_t cardType = SD.cardType();
  if (cardType == CARD_NONE) {
    halt("No SD card attached");
  }
}

static void getSsidListFromSD() {
  String w;
  int wifiCount = 0;

  File wifiFile = SD.open("/" WifiConf);
  if (!wifiFile) {
    halt("Failed to open file " WifiConf " for reading");
  }
  while (wifiFile.available()) {
    w = wifiFile.readStringUntil('\n');
    w.replace("\r", "");
    strncpy(WifiSsidList[wifiCount], w.c_str(), SSID_MAX_SIZE);
    w = wifiFile.readStringUntil('\n');
    w.replace("\r", "");
    strncpy(WifiPskList[wifiCount], w.c_str(), PSK_MAX_SIZE);
    ++wifiCount;
    if (wifiCount == MAX_SSID) break;
  }
  WifiSsidList[wifiCount][0] = 0;
  wifiFile.close();
}

static void connectWifi() {
  int waitCount;
  int wifiCount = 0;
  
  tft.println("Connect to WiFi.");
  for (;;) {
    WiFi.disconnect(); // delete old credentials
    tft.print("Trying ");
    tft.print(WifiSsidList[wifiCount]);
    tft.println(".");
    Serial.printf("Trying Wifi %s.\r\n", WifiSsidList[wifiCount]);
    WiFi.begin(WifiSsidList[wifiCount], WifiPskList[wifiCount]);
    waitCount = 0;
    for (;;) {
      if (WiFi.status() == WL_CONNECTED) goto connected;
      delay(500);
      ++waitCount;
      if (waitCount == 10) break;
    }
    ++wifiCount;
    if (WifiSsidList[wifiCount][0] == 0) break;
  }
  halt("No WiFi connection.");

connected:
  WifiSsid = WifiSsidList[wifiCount];
  WifiPsk = WifiPskList[wifiCount];
  tft.println("Connected.");
  Serial.print("MAC: ");
  Serial.println(WiFi.macAddress());
  Serial.print("SSID: ");
  Serial.println(WifiSsid);
  Serial.print("RSSI: ");
  Serial.println(WiFi.RSSI());
  delay(1000);
}

static void setServerFromSD() {
  String w;
  // get Server from SD
  File serverFile = SD.open("/" ServConf);
  if (!serverFile) {
    halt("Failed to open file " ServConf " for reading");
  }
  while (serverFile.available()) {
    w = serverFile.readStringUntil('\n');
    w.replace("\r", "");
    break;
  }
  serverFile.close();
  strncpy(Server, w.c_str(), SERV_MAX_SIZE);
  Serial.print("Server from SD: ");
  Serial.println(Server);
}

void serverConnect() {
  if (!client.connect(Server, ChatPort)) {
    Serial.println("Connection to host failed");
    delay(1000);
    return;
  }
  connected = true;
  client.write("listener:LOG ON||nopassword");
}

int serverRead() {
  if (connected) {
    int res = client.read(connectBuf, BUFSIZE);
    if (res == -1) {
      //Serial.println("[read from host failed]");
      *connectBuf = 0;
      return 1;
    } else {
      connectBuf[res] = 0;
      Serial.println((char*)connectBuf);
      return 0;
    }
  }
}

// unfortunately there are no good matching color bitmap draw methods available in this setup
// next 5 methods will implement reading from 24 bit PPM file because that's the most easiest solution
// and deliver 24 bit or 16 bit (RGB565) pixel from file

/**
 * Open PPM file, check header and on success read in image data to rgbBuf.
 * 
 * @param f The file object opened from SPIFFS or SD
 * @param width The width from PPM file will be stored here.
 * @param height The height from PPM file will be stored here.
 * @return 0 if no error, 1 PPM file format issue, 2 if not 8 bit per pixel, 3 size too big
 */
int readPpmHeader(File f, uint8_t *width, uint8_t *height) {
  uint8_t buf[PPM_HEADER_SIZE+2];
  ssize_t bytesRead;
  register uint8_t *p;
  register uint8_t *t;
  int x;

  *width = 0;
  *height = 0;
  p = buf;
  p[PPM_HEADER_SIZE] = '\n';
  p[PPM_HEADER_SIZE+1] = 0;
  //Serial.println("DEBUG: entering readPpmHeader()");
  bytesRead = f.readBytes((char *)p, PPM_HEADER_SIZE);
  if (bytesRead < 8) return 1;
  t = p + bytesRead - 2;
  //Serial.println("DEBUG: checking magic");
  /* magic bytes */
  if (*p != 'P') return 1;
  ++p;
  if ((*p < '1') || (*p > '6')) return 1;
  ++p;
  if (*p != '\n') return 1;
  ++p;
  /* comments */
  while (*p == '#') {
    if (p >= t) return 1;
    ++p;
    while (*p != '\n') {
      if (p >= t) return 1;
      ++p;
    }
    while (*p == '\n') {
      if (p >= t) return 1;
      ++p;
    }
  }
  /* width */
  if ((*p < '0') || (*p > '9')) return 1;
  x = atoi((const char *)p);
  //Serial.print("DEBUG: width: ");
  //Serial.println(x);
  if (x > 320) return 3;
  *width = (uint8_t) x;
  while (*p != ' ') {
    if (p >= t) return 1;
    ++p;
  }
  ++p;
  /* height */
  if ((*p < '0') || (*p > '9')) return 1;
  x = atoi((const char *)p);
  //Serial.print("DEBUG: height: ");
  //Serial.println(x);
  if (x > 240) return 3;
  *height = (uint8_t) x;
  while (*p != '\n') {
    if (p >= t) return 1;
    ++p;
  }
  ++p;
  /* values per channel */
  if ((*p < '0') || (*p > '9')) return 1;
  x = atoi((const char *)p);
  //Serial.print("DEBUG: depth: ");
  //Serial.println(x);
  if (x != 255) return 2;
  p += 4;
  /* seek back to point to image data */
  f.seek(p-buf);
  bytesRead = f.readBytes((char *)rgbBuf, BUFSIZE);
  rgbCursor = 0;
  return 0;
}

uint8_t getNextRgbByte() {
  uint8_t b = rgbBuf[rgbCursor];
  ++rgbCursor;
  if (rgbCursor > BUFSIZE) rgbCursor = 0;
  return b;
}
  
uint32_t getNextRgb24Pixel() {
  /* don't use an union because of unknown endianess, use bit shift */
  uint32_t rgb;
  rgb = getNextRgbByte() << 16;
  rgb |= getNextRgbByte() << 8;
  rgb |= getNextRgbByte();
  return rgb;
}

/**
 * @return Next pixel in RGB565 color
 */
uint16_t getNextRgb16Pixel() {
  uint16_t rgb;
  uint8_t x;
  x = getNextRgbByte() >> 3;
  rgb = x << 11;
  x = getNextRgbByte() >> 2;
  rgb |= x << 5;
  x = getNextRgbByte() >> 3;
  rgb |= x;
  return rgb;
}

void drawPpmBitmap(const char *filename) {
  File logoFile = SPIFFS.open(filename, "r");
  uint8_t ppmWidth, ppmHeight;
  //Serial.print("DEBUG: result from readPpmHeader: ");
  //Serial.println(readPpmHeader(logoFile, &ppmWidth, &ppmHeight));
  if (readPpmHeader(logoFile, &ppmWidth, &ppmHeight) == 0) {
    for (int row = 0; row < ppmHeight; row++) {
      for (int col = 0; col < ppmWidth; col++) {
        tft.drawPixel(0 + col, 0 + row, getNextRgb16Pixel());
      }
    }
  }
}




static void initializeScreen() {
  tft.setRotation(3);
  tft.fillScreen(TFT_BLACK);
  tft.setTextWrap(true, true);
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.setCursor(0, 0);
}

static void printLoad(int x, int y, const char *label, double load, const char *cpu, int *doBeep) {
  tft.setCursor(x, y);
  tft.setTextColor(TFT_WHITE, TFT_BLACK);
  tft.print(label);
  tft.setCursor(x+45, y);
  if (load >= 6) {
    tft.setTextColor(TFT_RED, TFT_BLACK);
    (*doBeep)++;
  } else {
    if (load >= 3) {
      tft.setTextColor(TFT_YELLOW, TFT_BLACK);
      (*doBeep)++;
    } else {
      tft.setTextColor(TFT_GREEN, TFT_BLACK);
    }
  }
  tft.print(load);
  tft.print(" ");
  tft.print(cpu);
}

static void showScreen() {
  initializeScreen();
  tft.loadFont(FONT);

  tft.setTextColor(TFT_WHITE, TFT_BLACK);
//  tft.setCursor(145, 3);
//  tft.println(TimeStrDate);
//  tft.setCursor(145, 31);
//  tft.println(TimeStrClock);

  int doBeep = 0;
  int x = 0;
  int y = 57;
  tft.setCursor(x, y);

  int offsetHost = 20;
  int offsetHdr = 0;
  //tft.setTextColor(0x39FF, TFT_BLACK);
  //tft.setTextColor(0x421F, TFT_BLACK);
  //tft.setTextColor(0x7BFF, TFT_BLACK);
  //printLoad(x, y+offsetHdr, "32: ", load_s02, cpu_s02, &doBeep);
  //printLoad(x, offsetHost+y+offsetHdr, "33: ", load_s03, cpu_s03, &doBeep);
  //printLoad(x, (2*offsetHost)+y+offsetHdr, "34: ", load_s04, cpu_s04, &doBeep);
  //tft.print("Please check serial out.");
  tft.print((char*)connectBuf);

  drawPpmBitmap(LOGO_FILE);

  tft.unloadFont();

//  if (doBeep != 0) {
//    beep();
//  }
}

void getHostByName(const char *name, ip_addr_t *ip) {
  err_t dns_result;
  int dnswait = 6;

  for (;;) {
    // don't use callback - instead simply poll and check for ERR_INPROGRESS
    dns_result = dns_gethostbyname(name, ip, 0, 0);
    Serial.printf("dns_gethostbyname %s: %d\r\n", name, dns_result);
    if (dns_result != ERR_INPROGRESS) {
      break;
    }
    --dnswait;
    if (dnswait == 0) {
      Serial.println("timeout");
      return;
    }
    delay(500);
  }
}

void setupDns() {
  char buf[31];
  ip_addr_t ip;
  char *p;
  *buf = 0;

  /* first try it with given DNS resolver */
  Serial.printf("trying to get IP# via local DNS resolver set by WiFi");
  getHostByName(ChatServer, &ip);
  ipaddr_ntoa_r(&ip, buf, 30);

  if (*buf == '0') {
    /* fallback: if local DNS resolver did not work then try to query DynDNS server directly */
    Serial.printf("fallback: trying to get IP# directly from DynDNS server");
    ipaddr_aton(DynDnsServer, &ip);
    dns_setserver(0, &ip);
    getHostByName(ChatServer, &ip);
  }

  strncpy(Server, ipaddr_ntoa_r(&ip, buf, 30), STRING_SIZE);
  Serial.printf("address: %s\r\n", Server);
}

static void beep() {
  ledcSetup(TONE_PIN_CHANNEL, 0, 13);
  ledcAttachPin(SPEAKER_PIN, TONE_PIN_CHANNEL);
  pinMode(25, OUTPUT);
  digitalWrite(25, HIGH);  ledcWriteTone(TONE_PIN_CHANNEL, 1000);
  delay(200);
  ledcWriteTone(TONE_PIN_CHANNEL, 0);
  digitalWrite(SPEAKER_PIN, 0);
}

void setup(void) {
  Serial.begin(115200); // Used for messages
  pinMode(PIN_BLUE_LED, OUTPUT);
  digitalWrite(PIN_BLUE_LED, HIGH);

  checkSpiffs();

  // Initialise the SD library before the TFT so the chip select is defined
  initializeSD();

  tft.init();
  initializeScreen();
  tft.loadFont(FONT_SMALL);

  getSsidListFromSD();
  if (!UseDynDns) {
    setServerFromSD();
  }

  connectWifi();

  if (UseDynDns) {
    setupDns();
  }

  strcpy((char*)connectBuf, "Please check serial out.");
  serverConnect();  
  showScreen();
}

void loop() {
  delay(2000);  
  if (!serverRead()) {
    showScreen();
  }
}
