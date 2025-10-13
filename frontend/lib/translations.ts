export type Language = "en" | "vn"

export const translations = {
  en: {
    // Topbar
    darkMode: "Dark Mode",
    lightMode: "Light Mode",
    language: "Language",

    // Index Panel
    indexName: "Index Name",
    importPDF: "Import PDF",
    buildIndex: "Build Index",
    loadSavedIndex: "Load Saved Index",
    addToIndex: "Add To Index",
    clearIndex: "Clear Index",
    dragDropArea: "Drag & drop PDF files here",
    orClick: "or click to browse",

    // Chat Panel
    chatTitle: "Chat",
    typeMessage: "Type your message...",
    send: "Send",
    saveChatHistory: "Save chat history locally",
    promptSuggestions: "Prompt Suggestions",

    // Model Thoughts Panel
    modelThoughts: "Model Thoughts",
    noThoughts: "Model reasoning will appear here...",

    // Status messages
    indexBuilt: "Index built successfully",
    indexCleared: "Index cleared",
    pdfImported: "PDF imported",
  },
  vn: {
    // Topbar
    darkMode: "Chế độ tối",
    lightMode: "Chế độ sáng",
    language: "Ngôn ngữ",

    // Index Panel
    indexName: "Tên chỉ mục",
    importPDF: "Nhập PDF",
    buildIndex: "Xây dựng chỉ mục",
    loadSavedIndex: "Tải chỉ mục đã lưu",
    addToIndex: "Thêm vào chỉ mục",
    clearIndex: "Xóa chỉ mục",
    dragDropArea: "Kéo thả tệp PDF vào đây",
    orClick: "hoặc nhấp để chọn",

    // Chat Panel
    chatTitle: "Trò chuyện",
    typeMessage: "Nhập tin nhắn của bạn...",
    send: "Gửi",
    saveChatHistory: "Lưu lịch sử trò chuyện cục bộ",
    promptSuggestions: "Gợi ý câu hỏi",

    // Model Thoughts Panel
    modelThoughts: "Suy nghĩ của mô hình",
    noThoughts: "Lý luận của mô hình sẽ xuất hiện ở đây...",

    // Status messages
    indexBuilt: "Đã xây dựng chỉ mục thành công",
    indexCleared: "Đã xóa chỉ mục",
    pdfImported: "Đã nhập PDF",
  },
}

export function getTranslation(lang: Language, key: keyof typeof translations.en): string {
  return translations[lang][key] || translations.en[key]
}
