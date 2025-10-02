import { PdfDoc, DocumentSelection, Insights, Recommendation, PodcastAudio } from '@/types';

// Mock AI service responses with realistic delays
export const aiService = {
  async summarizeDoc(doc: PdfDoc): Promise<string> {
    await delay(1500);
    return `AI-generated summary will appear after processing`;
  },

  async insightsFor(docOrSelection: PdfDoc | DocumentSelection): Promise<Insights> {
    await delay(2000);
    
    const isSelection = 'text' in docOrSelection;
    const context = isSelection ? docOrSelection.text : (docOrSelection as PdfDoc).name;
    
    return {
      keyInsights: [
        `This document presents novel approaches to ${context} with 15% performance improvement`,
        `The methodology section on page 12 contains critical implementation details`,
        `Figure 3 on page 8 shows the most significant results for your research focus`,
        `Key finding about ${context.substring(0, 30)}... demonstrates breakthrough potential`
      ],
      didYouKnow: [
        `The authors previously published 3 related papers on this topic in 2023`,
        `This approach has been cited by 127 other researchers in the past year`,
        `Similar methodologies are being explored by teams at MIT and Stanford`,
        `The first neural network was created in 1943`
      ],
      contradictions: [
        `Some studies suggest more data isn't always better`,
        `Figure 2 contradicts findings from earlier sections`,
        `The conclusion differs from the hypothesis presented in the introduction`,
        `Alternative approaches show conflicting results in recent literature`
      ],
      connections: [
        `Relates to Johnson et al. (2023) work on optimization techniques`,
        `Connects with emerging trends in computational efficiency research`,
        `Similar patterns found in your document "Learn Acrobat - Generative AI_1.pdf"`,
        `Cross-references with methodology from page 74 of related documents`
      ]
    };
  },

  async recommendationsFor(docOrSelection: PdfDoc | DocumentSelection): Promise<Recommendation[]> {
    await delay(1000);
    
    const isSelection = 'text' in docOrSelection;
    
    if (isSelection) {
      // Recommendations for selected text
      const selection = docOrSelection as DocumentSelection;
      return [
        {
          id: '1',
          title: `Deep dive analysis of "${selection.text.substring(0, 30)}..."`,
          description: `Explore the theoretical foundations and practical applications of the selected concept. This recommendation analyzes the content from page ${selection.page}.`,
          page: Math.max(1, selection.page + 5),
          match: 99
        },
        {
          id: '2',
          title: 'Cross-reference with related methodology',
          description: `Compare this approach with similar methodologies discussed elsewhere. Understanding these connections will enhance your comprehension.`,
          page: Math.max(1, selection.page + 10),
          match: 98
        },
        {
          id: '3',
          title: 'Implementation case studies',
          description: `Review practical examples that demonstrate real-world applications of these concepts.`,
          page: Math.max(1, selection.page - 3),
          match: 87
        }
      ];
    } else {
      // Recommendations for overall document
      const doc = docOrSelection as PdfDoc;
      return [
        {
          id: '1',
          title: 'Introduction and Overview',
          description: `Start with the document overview to understand the main concepts and structure. Essential reading for ${doc.name}.`,
          page: 1,
          match: 95
        },
        {
          id: '2',
          title: 'Methodology Section',
          description: 'Dive into the core methodology that explains the approach and techniques used in this document.',
          page: Math.min(doc.pages, 12),
          match: 92
        },
        {
          id: '3',
          title: 'Key Results and Findings',
          description: 'Review the most important results and findings that demonstrate the main outcomes.',
          page: Math.min(doc.pages, Math.floor(doc.pages * 0.6)),
          match: 89
        },
        {
          id: '4',
          title: 'Conclusion and Future Work',
          description: 'Understand the implications and future directions discussed in the conclusion.',
          page: Math.max(1, doc.pages - 2),
          match: 85
        }
      ];
    }
  },

  async podcastFor(docOrSelection: PdfDoc | DocumentSelection): Promise<PodcastAudio> {
    await delay(3000);
    
    // Create a simple audio blob with sine wave for demo
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    const sampleRate = audioContext.sampleRate;
    const duration = 3.75; // 3:45 duration
    const numSamples = sampleRate * duration;
    
    const audioBuffer = audioContext.createBuffer(2, numSamples, sampleRate);
    
    for (let channel = 0; channel < audioBuffer.numberOfChannels; channel++) {
      const channelData = audioBuffer.getChannelData(channel);
      for (let i = 0; i < numSamples; i++) {
        // Create a simple tone pattern to simulate speech
        const frequency = 200 + Math.sin(i / 5000) * 100;
        const amplitude = 0.1 * Math.sin(i / 10000);
        channelData[i] = amplitude * Math.sin(2 * Math.PI * frequency * i / sampleRate);
      }
    }
    
    // Convert to WAV blob
    const wav = audioBufferToWav(audioBuffer);
    const blob = new Blob([wav], { type: 'audio/wav' });
    const url = URL.createObjectURL(blob);
    
    return {
      blob,
      duration,
      url
    };
  }
};

function delay(ms: number): Promise<void> {
  return new Promise(resolve => setTimeout(resolve, ms));
}

// Simple audio buffer to WAV conversion
function audioBufferToWav(buffer: AudioBuffer): ArrayBuffer {
  const length = buffer.length * buffer.numberOfChannels * 2;
  const arrayBuffer = new ArrayBuffer(44 + length);
  const view = new DataView(arrayBuffer);
  
  // WAV header
  const writeString = (offset: number, string: string) => {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  };
  
  writeString(0, 'RIFF');
  view.setUint32(4, 36 + length, true);
  writeString(8, 'WAVE');
  writeString(12, 'fmt ');
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, buffer.numberOfChannels, true);
  view.setUint32(24, buffer.sampleRate, true);
  view.setUint32(28, buffer.sampleRate * buffer.numberOfChannels * 2, true);
  view.setUint16(32, buffer.numberOfChannels * 2, true);
  view.setUint16(34, 16, true);
  writeString(36, 'data');
  view.setUint32(40, length, true);
  
  // Convert float samples to 16-bit PCM
  const channels = [];
  for (let i = 0; i < buffer.numberOfChannels; i++) {
    channels.push(buffer.getChannelData(i));
  }
  
  let offset = 44;
  for (let i = 0; i < buffer.length; i++) {
    for (let channel = 0; channel < buffer.numberOfChannels; channel++) {
      const sample = Math.max(-1, Math.min(1, channels[channel][i]));
      view.setInt16(offset, sample * 0x7FFF, true);
      offset += 2;
    }
  }
  
  return arrayBuffer;
}