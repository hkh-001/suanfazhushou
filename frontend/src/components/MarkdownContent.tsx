import ReactMarkdown, { type Components } from "react-markdown";
import rehypeHighlight from "rehype-highlight";
import rehypeKatex from "rehype-katex";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";

type MarkdownContentProps = {
  content: string;
  className?: string;
};

const markdownComponents: Components = {
  a: ({ children, href, title, className }) => {
    const external = href?.startsWith("http://") || href?.startsWith("https://");

    return (
      <a
        className={className}
        href={href}
        rel={external ? "noreferrer noopener" : undefined}
        target={external ? "_blank" : undefined}
        title={title}
      >
        {children}
      </a>
    );
  },
  h1: ({ children, id, className }) => (
    <h3 className={className} id={id}>
      {children}
    </h3>
  ),
  h2: ({ children, id, className }) => (
    <h4 className={className} id={id}>
      {children}
    </h4>
  ),
  h3: ({ children, id, className }) => (
    <h5 className={className} id={id}>
      {children}
    </h5>
  ),
  table: ({ children, className }) => (
    <div className="my-6 overflow-x-auto rounded-lg border border-slate-200">
      <table className={className}>{children}</table>
    </div>
  ),
  pre: ({ children, className }) => (
    <pre
      className={`overflow-x-auto rounded-lg border border-slate-200 bg-slate-50 p-4 text-sm leading-6 shadow-inner shadow-slate-100 ${className ?? ""}`}
    >
      {children}
    </pre>
  )
};

export function MarkdownContent({ content, className = "" }: MarkdownContentProps) {
  return (
    <div
      className={`prose prose-slate max-w-none prose-headings:scroll-mt-24 prose-headings:text-slate-950 prose-a:text-blue-600 prose-a:no-underline hover:prose-a:underline prose-pre:overflow-x-auto prose-pre:bg-transparent prose-pre:p-0 prose-code:before:content-none prose-code:after:content-none prose-table:min-w-[36rem] ${className}`}
    >
      <ReactMarkdown
        components={markdownComponents}
        rehypePlugins={[rehypeKatex, [rehypeHighlight, { detect: true }]]}
        remarkPlugins={[remarkGfm, remarkMath]}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
