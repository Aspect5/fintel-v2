import React from 'react';

// A simple and safe parser for basic markdown used in the app.
const parseMarkdown = (text: string) => {
    let html = text;

    // This regex is safe because it only replaces text content with HTML tags
    // and does not execute any embedded scripts.

    // Headers: ## text -> <h2>text</h2>
    html = html.replace(/^## (.*$)/gm, '<h2 class="text-lg font-semibold text-brand-text-primary mb-2 mt-4">$1</h2>');
    html = html.replace(/^### (.*$)/gm, '<h3 class="text-md font-semibold text-brand-text-primary mb-2 mt-3">$1</h3>');
    
    // Bold: **text** -> <strong>text</strong>
    // Using a non-greedy match (.*?) to handle multiple bolds on one line.
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong class="font-semibold">$1</strong>');
    
    // Italic: *text* -> <em>text</em>
    html = html.replace(/\*(.*?)\*/g, '<em class="italic">$1</em>');
    
    // Lists: - item -> <li>item</li>
    html = html.replace(/^- (.*$)/gm, '<li class="ml-4 mb-1">$1</li>');
    html = html.replace(/^(\d+)\. (.*$)/gm, '<li class="ml-4 mb-1">$2</li>');
    
    // Wrap lists in <ul> or <ol>
    html = html.replace(/(<li.*<\/li>)/gs, '<ul class="list-disc list-inside mb-3">$1</ul>');
    
    // Newlines -> <br>
    html = html.replace(/\n/g, '<br />');
    
    // Clean up multiple <br> tags
    html = html.replace(/<br \/>\s*<br \/>/g, '<br />');

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
            className={`text-sm leading-relaxed ${className || ''}`}
            dangerouslySetInnerHTML={{ __html: sanitizedHtml }} 
        />
    );
};

export default MarkdownRenderer;
