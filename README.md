# code arduino
                                #include <Wire.h>
                                #include <Adafruit_Sensor.h>
                                #include <Adafruit_BME280.h>
                                #include <BH1750.h>
                                #include <WiFiClientSecure.h>
                                #include <WiFi.h>
                                #include <PubSubClient.h>
                                
                                // Sertifikat TLS Let's Encrypt (ISRG Root X1)
                                const char root_ca[] PROGMEM = R"EOF(
                                -----BEGIN CERTIFICATE-----
                                MIIFazCCA1OgAwIBAgIRAIIQz7DSQONZRGPgu2OCiwAwDQYJKoZIhvcNAQELBQAw
                                TzELMAkGA1UEBhMCVVMxKTAnBgNVBAoTIEludGVybmV0IFNlY3VyaXR5IFJlc2Vh
                                cmNoIEdyb3VwMRUwEwYDVQQDEwxJU1JHIFJvb3QgWDEwHhcNMTUwNjA0MTEwNDM4
                                WhcNMzUwNjA0MTEwNDM4WjBPMQswCQYDVQQGEwJVUzEpMCcGA1UEChMgSW50ZXJu
                                ZXQgU2VjdXJpdHkgUmVzZWFyY2ggR3JvdXAxFTATBgNVBAMTDElTUkcgUm9vdCBY
                                MTCCAiIwDQYJKoZIhvcNAQEBBQADggIPADCCAgoCggIBAK3oJHP0FDfzm54rVygc
                                h77ct984kIxuPOZXoHj3dcKi/vVqbvYATyjb3miGbESTtrFj/RQSa78f0uoxmyF+
                                0TM8ukj13Xnfs7j/EvEhmkvBioZxaUpmZmyPfjxwv60pIgbz5MDmgK7iS4+3mX6U
                                A5/TR5d8mUgjU+g4rk8Kb4Mu0UlXjIB0ttov0DiNewNwIRt18jA8+o+u3dpjq+sW
                                T8KOEUt+zwvo/7V3LvSye0rgTBIlDHCNAymg4VMk7BPZ7hm/ELNKjD+Jo2FR3qyH
                                B5T0Y3HsLuJvW5iB4YlcNHlsdu87kGJ55tukmi8mxdAQ4Q7e2RCOFvu396j3x+UC
                                B5iPNgiV5+I3lg02dZ77DnKxHZu8A/lJBdiB3QW0KtZB6awBdpUKD9jf1b0SHzUv
                                KBds0pjBqAlkd25HN7rOrFleaJ1/ctaJxQZBKT5ZPt0m9STJEadao0xAH0ahmbWn
                                OlFuhjuefXKnEgV4We0+UXgVCwOPjdAvBbI+e0ocS3MFEvzG6uBQE3xDk3SzynTn
                                jh8BCNAw1FtxNrQHusEwMFxIt4I7mKZ9YIqioymCzLq9gwQbooMDQaHWBfEbwrbw
                                qHyGO0aoSCqI3Haadr8faqU9GY/rOPNk3sgrDQoo//fb4hVC1CLQJ13hef4Y53CI
                                rU7m2Ys6xt0nUW7/vGT1M0NPAgMBAAGjQjBAMA4GA1UdDwEB/wQEAwIBBjAPBgNV
                                HRMBAf8EBTADAQH/MB0GA1UdDgQWBBR5tFnme7bl5AFzgAiIyBpY9umbbjANBgkq
                                hkiG9w0BAQsFAAOCAgEAVR9YqbyyqFDQDLHYGmkgJykIrGF1XIpu+ILlaS/V9lZL
                                ubhzEFnTIZd+50xx+7LSYK05qAvqFyFWhfFQDlnrzuBZ6brJFe+GnY+EgPbk6ZGQ
                                3BebYhtF8GaV0nxvwuo77x/Py9auJ/GpsMiu/X1+mvoiBOv/2X/qkSsisRcOj/KK
                                NFtY2PwByVS5uCbMiogziUwthDyC3+6WVwW6LLv3xLfHTjuCvjHIInNzktHCgKQ5
                                ORAzI4JMPJ+GslWYHb4phowim57iaztXOoJwTdwJx4nLCgdNbOhdjsnvzqvHu7Ur
                                TkXWStAmzOVyyghqpZXjFaH3pO3JLF+l+/+sKAIuvtd7u+Nxe5AW0wdeRlN8NwdC
                                jNPElpzVmbUq4JUagEiuTDkHzsxHpFKVK7q4+63SM1N95R1NbdWhscdCb+ZAJzVc
                                oyi3B43njTOQ5yOf+1CceWxG1bQVs5ZufpsMljq4Ui0/1lvh+wjChP4kqKOJ2qxq
                                4RgqsahDYVvTH9w7jXbyLeiNdd8XM2w9U/t7y0Ff/9yi0GE44Za4rF2LN9d11TPA
                                mRGunUHBcnWEvgJBQl9nJEiU0Zsnvgc/ubhPgXRR4Xq37Z0j4r7g1SgEEzwxA57d
                                emyPxgcYxn/eR44/KJ4EBs+lVDR3veyJm+kXQ99b21/+jh5Xos1AnX5iItreGCc=
                                -----END CERTIFICATE-----
                                )EOF";
                                
                                // Pin Sensor
                                #define SDA_PIN 9
                                #define SCL_PIN 8
                                #define MQ135_PIN 10
                                #define TRIG_PIN 6
                                #define ECHO_PIN 7
                                #define BUZZER_PIN 5
                                #define LED_PIN 13
                                
                                // WiFi dan MQTT
                                const char* ssidList[] = {"xiaomi 12", "Universitas Pelita Bangsa New", "GEORGIA"};
                                const char* passwordList[] = {"12345678", "megah123", "Georgia12345"};
                                const char* mqtt_server = "";
                                const int mqtt_port = 8883;
                                const char* mqtt_user = "irsyad26";
                                const char* mqtt_pass = "Irsyad261203";
                                const char* mqtt_topic = "iot/esp32/data";
                                
                                WiFiClientSecure secureClient;
                                PubSubClient client(secureClient);
                                Adafruit_BME280 bme;
                                BH1750 lightMeter;
                                
                                unsigned long lastSendTime = 0;
                                unsigned long lastReconnectAttempt = 0;
                                bool buzzerOn = false;
                                unsigned long lastHighPPMTime = 0;
                                
                                float getDistanceCM() {
                                  digitalWrite(TRIG_PIN, LOW);
                                  delayMicroseconds(2);
                                  digitalWrite(TRIG_PIN, HIGH);
                                  delayMicroseconds(10);
                                  digitalWrite(TRIG_PIN, LOW);
                                  long duration = pulseIn(ECHO_PIN, HIGH, 30000);
                                  return (duration > 0) ? (duration * 0.0343) / 2 : -1;
                                }
                                
                                void connectToWiFi() {
                                  for (int i = 0; i < 3; i++) {
                                    WiFi.begin(ssidList[i], passwordList[i]);
                                    Serial.printf("Mencoba SSID: %s\n", ssidList[i]);
                                    for (int retry = 0; retry < 20 && WiFi.status() != WL_CONNECTED; retry++) {
                                      delay(500);
                                      Serial.print(".");
                                    }
                                    if (WiFi.status() == WL_CONNECTED) {
                                      Serial.printf("\n✅ Terhubung ke WiFi! IP: %s\n", WiFi.localIP().toString().c_str());
                                      return;
                                    }
                                    Serial.println("\nGagal. Coba SSID berikutnya...");
                                  }
                                  Serial.println("❌ Tidak bisa konek ke jaringan manapun.");
                                }
                                
                                void callback(char* topic, byte* payload, unsigned int length) {
                                  Serial.print("📥 Pesan dari MQTT: ");
                                  for (int i = 0; i < length; i++) Serial.print((char)payload[i]);
                                  Serial.println();
                                }
                                
                                void reconnectMQTT() {
                                  if (!client.connected()) {
                                    Serial.print("🔄 Reconnect MQTT...");
                                    if (client.connect("ESP32Client", mqtt_user, mqtt_pass)) {
                                      Serial.println("✅ MQTT Connected");
                                      client.subscribe(mqtt_topic); // jika ingin menerima
                                    } else {
                                      Serial.printf("❌ Gagal: %s\n", client.state());
                                    }
                                  }
                                }
                                
                                void setup() {
                                  Serial.begin(115200);
                                  Wire.begin(SDA_PIN, SCL_PIN);
                                  pinMode(TRIG_PIN, OUTPUT);
                                  pinMode(ECHO_PIN, INPUT);
                                  pinMode(BUZZER_PIN, OUTPUT);
                                  pinMode(LED_PIN, OUTPUT);
                                  analogReadResolution(12);
                                
                                  connectToWiFi();
                                
                                  secureClient.setCACert(root_ca);
                                  client.setServer(mqtt_server, mqtt_port);
                                  client.setCallback(callback);
                                
                                  bool bmeOK = bme.begin(0x76);
                                  bool bhOK = lightMeter.begin();
                                  if (!bmeOK || !bhOK) {
                                    Serial.println("⚠️ Sensor error, lanjutkan tapi data mungkin tidak lengkap.");
                                  }
                                }
                                
                                void loop() {
                                  if (WiFi.status() != WL_CONNECTED) {
                                    connectToWiFi();
                                    delay(1000);
                                    return;
                                  }
                                
                                  if (!client.connected()) {
                                    unsigned long now = millis();
                                    if (now - lastReconnectAttempt > 5000) {
                                      lastReconnectAttempt = now;
                                      reconnectMQTT();
                                    }
                                  } else {
                                    client.loop();
                                  }
                                
                                  unsigned long now = millis();
                                  if (now - lastSendTime >= 1000) {
                                    lastSendTime = now;
                                
                                    float suhu = bme.readTemperature();
                                    float kelembapan = bme.readHumidity();
                                    float tekanan = bme.readPressure() / 100.0F;
                                    float altitude = bme.readAltitude(1013.25);
                                    float lightLevel = lightMeter.readLightLevel();
                                    int mq135_raw = analogRead(MQ135_PIN);
                                    float mq135_ppm = map(mq135_raw, 0, 4095, 0, 1000);
                                    float jarak = getDistanceCM();
                                
                                    if (mq135_ppm > 200) {
                                      if (!buzzerOn && now - lastHighPPMTime >= 5000) {
                                        digitalWrite(BUZZER_PIN, HIGH);
                                        buzzerOn = true;
                                        Serial.println("🚨 Buzzer ON (PPM tinggi)");
                                      } else if (!buzzerOn && lastHighPPMTime == 0) {
                                        lastHighPPMTime = now;
                                      }
                                    } else {
                                      digitalWrite(BUZZER_PIN, LOW);
                                      if (buzzerOn) Serial.println("✅ PPM turun, buzzer OFF");
                                      buzzerOn = false;
                                      lastHighPPMTime = 0;
                                    }
                                
                                    String payload = "{\"suhu\": " + String(suhu, 2) +
                                                     ", \"kelembapan\": " + String(kelembapan, 2) +
                                                     ", \"tekanan\": " + String(tekanan, 2) +
                                                     ", \"altitude\": " + String(altitude, 2) +
                                                     ", \"mq135_ppm\": " + String(mq135_ppm, 2) +
                                                     ", \"jarak_ultrasonik\": " + String(jarak, 2) +
                                                     ", \"light_level\": " + String(lightLevel, 2) + "}";
                                
                                    if (client.publish(mqtt_topic, payload.c_str())) {
                                      digitalWrite(LED_PIN, !digitalRead(LED_PIN)); // Toggle LED tiap publish
                                      Serial.println("📤 Data MQTT terkirim");
                                    } else {
                                      Serial.println("❌ Gagal kirim MQTT");
                                    }
                                  }
                                }
