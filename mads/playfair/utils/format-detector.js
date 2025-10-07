/**
 * Auto-detects the diagram format based on content heuristics.
 */
const formatDetector = {
    detect(content) {
        const trimmedContent = content.trim();

        // Graphviz (DOT) heuristics
        if (trimmedContent.match(/^(strict\s+)?(di)?graph\s*\{/i)) {
            return 'dot';
        }

        // Mermaid heuristics
        const mermaidKeywords = [
            'graph',
            'flowchart',
            'sequenceDiagram',
            'stateDiagram',
            'erDiagram',
            'mindmap',
            'gantt',
            'pie'
        ];
        if (mermaidKeywords.some(kw => trimmedContent.startsWith(kw))) {
            return 'mermaid';
        }

        return null; // Detection failed
    }
};

module.exports = formatDetector;