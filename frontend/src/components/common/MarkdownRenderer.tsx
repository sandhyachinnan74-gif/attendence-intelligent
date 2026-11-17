import React from 'react';
import { Lightbulb, AlertTriangle, CheckCircle, Database } from 'lucide-react';

interface MarkdownRendererProps {
  content: string;
}

export const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content }) => {
  if (!content) return null;

  // Split into paragraphs / blocks
  const lines = content.split('\n');
  const elements: React.ReactNode[] = [];
  let tableRows: string[] = [];
  let inTable = false;
  let keyIndex = 0;

  const flushTable = () => {
    if (tableRows.length > 0) {
      const headerLine = tableRows[0];
      const dataLines = tableRows.slice(2); // Skip separator line

      const headers = headerLine
        .split('|')
        .map((h) => h.trim())
        .filter((h) => h.length > 0);

      elements.push(
        <div key={`table-${keyIndex++}`} className="my-3 overflow-x-auto rounded-lg border border-border bg-white shadow-xs">
          <table className="w-full text-left text-xs border-collapse">
            <thead>
              <tr className="bg-slate-100/80 border-b border-border">
                {headers.map((h, i) => (
                  <th key={i} className="py-2 px-3 font-semibold text-dark text-[11px] tracking-wide">
                    {renderInlineFormatting(h)}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody className="divide-y divide-border/60">
              {dataLines.map((row, rIdx) => {
                const cells = row
                  .split('|')
                  .map((c) => c.trim())
                  .filter((c) => c.length > 0);
                if (cells.length === 0) return null;
                return (
                  <tr key={rIdx} className="hover:bg-slate-50/80 transition-colors">
                    {cells.map((cell, cIdx) => (
                      <td key={cIdx} className="py-2 px-3 text-secondary text-[11.5px] leading-relaxed">
                        {renderInlineFormatting(cell)}
                      </td>
                    ))}
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      );
      tableRows = [];
      inTable = false;
    }
  };

  const renderInlineFormatting = (text: string): React.ReactNode => {
    // Process bold **text**, code `text`, and italic *text*
    const parts = text.split(/(\*\*.*?\*\*|`.*?`|\*.*?\*)/g);
    return parts.map((part, idx) => {
      if (part.startsWith('**') && part.endsWith('**')) {
        return (
          <strong key={idx} className="font-semibold text-dark">
            {part.slice(2, -2)}
          </strong>
        );
      }
      if (part.startsWith('`') && part.endsWith('`')) {
        return (
          <code key={idx} className="px-1.5 py-0.5 rounded bg-slate-100 font-mono text-[11px] text-primary font-medium">
            {part.slice(1, -1)}
          </code>
        );
      }
      if (part.startsWith('*') && part.endsWith('*')) {
        return (
          <em key={idx} className="italic text-secondary">
            {part.slice(1, -1)}
          </em>
        );
      }
      return part;
    });
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    const trimmed = line.trim();

    // Table check
    if (trimmed.startsWith('|') && trimmed.endsWith('|')) {
      inTable = true;
      tableRows.push(trimmed);
      continue;
    } else if (inTable) {
      flushTable();
    }

    // Dividers
    if (trimmed === '---') {
      elements.push(<hr key={`hr-${keyIndex++}`} className="my-3 border-border/80" />);
      continue;
    }

    // Headings
    if (trimmed.startsWith('### ')) {
      const headingText = trimmed.replace('### ', '');
      const isInsight = headingText.toLowerCase().includes('insight') || headingText.toLowerCase().includes('observation');
      const isWarning = headingText.toLowerCase().includes('attention') || headingText.toLowerCase().includes('recommendation');

      elements.push(
        <div key={`h3-${keyIndex++}`} className="mt-3.5 mb-1.5 flex items-center gap-1.5">
          {isInsight && <Lightbulb className="w-4 h-4 text-amber-500 flex-shrink-0" />}
          {isWarning && <AlertTriangle className="w-4 h-4 text-primary flex-shrink-0" />}
          <h3 className="text-xs font-bold text-dark uppercase tracking-wider">{headingText}</h3>
        </div>
      );
      continue;
    }

    if (trimmed.startsWith('## ')) {
      elements.push(
        <h2 key={`h2-${keyIndex++}`} className="text-sm font-bold text-dark mt-4 mb-2 pb-1 border-b border-border">
          {trimmed.replace('## ', '')}
        </h2>
      );
      continue;
    }

    // Bullet points
    if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
      const bulletContent = trimmed.slice(2);
      elements.push(
        <div key={`bullet-${keyIndex++}`} className="flex items-start gap-2 my-1 text-xs leading-relaxed text-slate-700 pl-1">
          <span className="w-1.5 h-1.5 rounded-full bg-primary flex-shrink-0 mt-1.5" />
          <span>{renderInlineFormatting(bulletContent)}</span>
        </div>
      );
      continue;
    }

    // Standard paragraph / line
    if (trimmed.length > 0) {
      elements.push(
        <p key={`p-${keyIndex++}`} className="my-1 text-xs leading-relaxed text-slate-800">
          {renderInlineFormatting(trimmed)}
        </p>
      );
    }
  }

  if (inTable) {
    flushTable();
  }

  return <div className="space-y-1">{elements}</div>;
};
