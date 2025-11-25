self.addEventListener("install", (e) => {
  console.log("[Service Worker] Install");
});

self.addEventListener("fetch", (e) => {
  // Kita biarkan kosong agar request tetap online (karena ini downloader)
  // Tidak perlu cache offline untuk logic utamanya
});
