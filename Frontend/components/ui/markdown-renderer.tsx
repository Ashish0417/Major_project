import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'

interface MarkdownRendererProps {
  children: string;
}

export function MarkdownRenderer({ children }: MarkdownRendererProps) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        h1: ({ node, ...props }: any) => <h1 className="text-3xl font-bold mt-6 mb-4 text-foreground" {...props} />,
        h2: ({ node, ...props }: any) => <h2 className="text-2xl font-semibold mt-5 mb-3 text-foreground" {...props} />,
        h3: ({ node, ...props }: any) => <h3 className="text-xl font-semibold mt-4 mb-2 text-foreground" {...props} />,
        h4: ({ node, ...props }: any) => <h4 className="text-lg font-semibold mt-3 mb-2 text-foreground" {...props} />,
        strong: ({ node, ...props }: any) => <strong className="font-semibold text-foreground" {...props} />,
        p: ({ node, ...props }: any) => <p className="text-base leading-7 mb-4 text-muted-foreground" {...props} />,
        ul: ({ node, ...props }: any) => <ul className="list-disc pl-5 mb-4 space-y-1 text-muted-foreground" {...props} />,
        ol: ({ node, ...props }: any) => <ol className="list-decimal pl-5 mb-4 space-y-1 text-muted-foreground" {...props} />,
        li: ({ node, ...props }: any) => <li className="text-base leading-7" {...props} />,
        a: ({ node, ...props }: any) => <a className="text-primary hover:underline font-medium" {...props} />,
        blockquote: ({ node, ...props }: any) => (
          <blockquote className="border-l-4 border-muted-foreground/30 pl-4 italic my-4 text-muted-foreground" {...props} />
        ),
      }}
    >
      {children}
    </ReactMarkdown>
  )
}

export function CompactMarkdown({ children }: MarkdownRendererProps) {
  return (
    <ReactMarkdown
      remarkPlugins={[remarkGfm]}
      components={{
        h1: ({ node, ...props }: any) => <span className="font-bold" {...props} />,
        h2: ({ node, ...props }: any) => <span className="font-bold" {...props} />,
        h3: ({ node, ...props }: any) => <span className="font-bold" {...props} />,
        h4: ({ node, ...props }: any) => <span className="font-bold" {...props} />,
        strong: ({ node, ...props }: any) => <strong className="font-semibold" {...props} />,
        p: ({ node, ...props }: any) => <span className="inline" {...props} />,
        ul: ({ node, ...props }: any) => <span className="ml-1 inline" {...props} />,
        ol: ({ node, ...props }: any) => <span className="ml-1 inline" {...props} />,
        li: ({ node, ...props }: any) => <span className="mr-2 inline" {...props} />,
        a: ({ node, ...props }: any) => <span className="font-medium" {...props} />,
      }}
    >
      {children}
    </ReactMarkdown>
  )
}
