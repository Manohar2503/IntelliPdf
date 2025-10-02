import { PdfDoc } from '@/types';

export async function loadCurrentDocument(): Promise<PdfDoc | null> {
  try {
    // Assuming current_doc.json is served statically or accessible via a direct path
    const response = await fetch('/current_doc.json');
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    const data = await response.json();

    if (data && data.documents && data.documents.length > 0) {
      const docData = data.documents[0];
      // Concatenate content from all sections to form the full document content
      const fullContent = docData.sections.map((section: any) => section.content).join('\n\n');

      const pdfDoc: PdfDoc = {
        id: docData.doc_id,
        name: docData.title,
        content: fullContent,
        filePath: docData.file_path,
        url: docData.file_path, // Assign file_path to url
        sizeBytes: 0, // Placeholder, as sizeBytes is not in current_doc.json
        uploadedAt: new Date().toISOString(), // Placeholder
        summary: '', // Placeholder
        sections: docData.sections.map((section: any) => ({
          id: section.section_id,
          heading: section.heading,
          headingLevel: section.heading_level,
          pageNumber: section.page_number,
          content: section.content,
          snippets: section.snippets || []
        }))
      };
      return pdfDoc;
    }
    return null;
  } catch (error) {
    console.error('Error loading current document:', error);
    return null;
  }
}
