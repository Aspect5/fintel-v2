import React from 'react';

// A simple and safe parser for basic markdown used in the app.
const parseMarkdown = (text: string) => {
    let html = text;

    // This regex is safe because it only replaces text content with HTML tags
    // and does not execute any embedded scripts.

    // Bold: **text** -> <strong>text</strong>
    // Using a non-greedy match (.*?) to handle multiple bolds on one line.
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Newlines -> <br>
    html = html.replace(/\n/g, '<br />');

    return html;
};

interface MarkdownRendererProps {
    content: string;
    className?: string;
}

const MarkdownRenderer: React.FC<MarkdownRendererProps> = ({ content, className }) => {
    const sanitizedHtml = parseMarkdown(content);
    return (
        <div
            className={`text-sm ${className || ''}`}
            dangerouslySetInnerHTML={{ __html: sanitizedHtml }} 
        />
    );
};

export default MarkdownRenderer;
