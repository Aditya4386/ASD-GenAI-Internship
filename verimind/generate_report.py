import os
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

def add_heading(doc, text, level=1):
    h = doc.add_heading(text, level=level)
    # Style the heading
    if level == 1:
        for run in h.runs:
            run.font.size = Pt(16)
            run.bold = True
    elif level == 2:
        for run in h.runs:
            run.font.size = Pt(14)
            run.bold = True

def add_paragraph(doc, text, bold=False):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    run = p.add_run(text)
    if bold:
        run.bold = True
    return p

def create_report():
    doc = Document()

    # ── Title Page ──
    title = doc.add_paragraph()
    title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    run = title.add_run("VERIMIND: MULTI-AGENT DOCUMENT INTELLIGENCE PLATFORM\n\n\n")
    run.bold = True
    run.font.size = Pt(18)

    run2 = title.add_run("A Project Report\n\nIn the partial fulfilment of the award of the degree of\n\nB.Tech\n\nUnder\n\nAcademy of Skill Development\n\n\n\n")
    run2.font.size = Pt(14)
    run2.bold = True

    run3 = title.add_run("Submitted by:\n\nDEEPAM\nHARSH MAMGAI\nSHIVAM SHUBHAM\nROY & ARYAN\nTIWARI\n\n\n\n")
    run3.font.size = Pt(14)
    run3.bold = True

    run4 = title.add_run("BHARATI VIDYAPEETH COLLEGE OF ENGINEERING, NEW DELHI\n")
    run4.font.size = Pt(14)
    run4.bold = True

    doc.add_page_break()

    # ── Certificate ──
    cert_title = doc.add_paragraph()
    cert_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cr = cert_title.add_run("CERTIFICATE FROM THE MENTOR\n\n")
    cr.bold = True
    cr.font.size = Pt(16)

    add_paragraph(doc, "This is to certify that DEEPAM, HARSH MAMGAI, SHIVAM, SHUBHAM ROY & ARYAN TIWARI has completed the project titled VERIMIND: MULTI-AGENT DOCUMENT INTELLIGENCE PLATFORM under my supervision during the period from June to July which is in partial fulfilment of requirements for the award of the B.Tech and submitted to Department Information Technology of BHARATI VIDYAPEETH COLLEGE OF ENGINEERING.\n\n\n\n")
    
    sig_p = doc.add_paragraph()
    sig_p.add_run("DATE:                                                                                             Signature of the Mentor")
    sig_p.runs[0].bold = True
    doc.add_page_break()

    # ── Acknowledgment ──
    ack_title = doc.add_paragraph()
    ack_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    ar = ack_title.add_run("ACKNOWLEDGMENT\n\n")
    ar.bold = True
    ar.font.size = Pt(16)

    add_paragraph(doc, "I take this opportunity to express my deep gratitude and sincerest thanks to my project mentor, Mr. Mahendra Datta for giving the most valuable suggestions, helpful guidance, and encouragement in the execution of this project work.\n\nI would like to give a special mention to my colleagues. Last but not least I am grateful to all the faculty members of the Academy of Skill Development for their support.")
    doc.add_page_break()

    # ── Abstract ──
    add_heading(doc, "Abstract", level=1)
    add_paragraph(doc, "VeriMind is a state-of-the-art document intelligence platform designed to address the common shortcomings of Large Language Models (LLMs), such as hallucinations, logical inconsistencies, and lack of verifiable evidence. While standard Retrieval-Augmented Generation (RAG) provides context to LLMs, traditional single-pass pipelines often struggle with conflicting information or complex reasoning tasks.\n\nThis project explores the application of a Multi-Agent architecture to solve these challenges using LangGraph. VeriMind orchestrates a pipeline of specialized AI personas: an Answer Generator to draft the initial response, a Debater to find agreements and disagreements in the context, a Critic to score the draft and identify logical flaws, a Judge to synthesize the final revised answer, and a Verifier to fact-check against the source text and provide a final confidence score.\n\nBuilt with a FastAPI (Python) backend and a responsive React (Vite) frontend, VeriMind allows users to upload documents (PDF, TXT, DOCX), processes them into chunks, and stores embeddings in a local vector store for rapid retrieval. The evaluation of this multi-agent system demonstrates significantly higher factual accuracy, greater resilience to hallucination, and improved user trust compared to conventional single-agent generation systems.")
    doc.add_page_break()

    # ── Chapter 1 ──
    add_heading(doc, "Chapter 1: Introduction", level=1)
    add_paragraph(doc, "Document intelligence and question-answering systems have become critical tools for parsing large volumes of information. However, current AI models frequently produce hallucinated information when dealing with complex or unfamiliar texts.")
    
    add_heading(doc, "1.1 Background of RAG and Multi-Agent Systems", level=2)
    add_paragraph(doc, "Retrieval-Augmented Generation (RAG) techniques primarily utilize document embeddings to retrieve relevant text chunks, which are then passed to an LLM to generate an answer. These models, while effective, are limited by their single-pass nature. If the retrieved context is complex, the single generation step often fails to reason deeply or recognize its own mistakes. With the emergence of multi-agent workflows, LLMs can be assigned distinct roles to iteratively improve an output with minimal computational overhead compared to retraining models.")

    add_heading(doc, "1.2 Problem Statement", level=2)
    add_paragraph(doc, "Standard RAG models suffer from several limitations:\n• Dependence on a single generation pass leading to uncorrected hallucinations.\n• Inability to critically evaluate their own answers against the source text.\n• Limited ability to extract accurate citations and provide a reliable confidence score.\n\nThe integration of a multi-agent debate and critique mechanism presents a potential solution to these challenges. This project aims to develop an efficient and robust multi-agent RAG platform that overcomes the limitations of conventional single-pass methods.")

    add_heading(doc, "1.3 Objectives", level=2)
    add_paragraph(doc, "The primary objectives of this project are:\n1. To explore and analyze different multi-agent reasoning techniques applicable to document intelligence.\n2. To develop an efficient and effective FastAPI backend for document processing and vector retrieval.\n3. To construct a LangGraph-based agent pipeline comprising Generator, Debater, Critic, Judge, and Verifier agents.\n4. To implement a real-time streaming React frontend to visualize the agent pipeline and present the verified results.\n5. To compare the performance of the multi-agent approach against traditional single-pass RAG.")
    doc.add_page_break()

    # ── Chapter 2 ──
    add_heading(doc, "Chapter 2: Related Work", level=1)
    add_paragraph(doc, "In today's data-driven world, artificial intelligence plays a key role in information extraction. Researchers have successfully applied several architectures to improve LLM generation accuracy.\n\nLewis et al. (2020) proposed the original Retrieval-Augmented Generation (RAG) framework, combining pre-trained parametric and non-parametric memory for language generation. While successful, it lacked self-correction.\n\nAsai et al. (2023) proposed Self-RAG, a framework that learns to retrieve, generate, and critique through self-reflection. It trains an LM to generate reflection tokens to assess retrieval quality and generation accuracy.\n\nMore recently, Multi-Agent Debate frameworks (Du et al., 2023) have shown that having multiple LLM instances debate a topic leads to more factual and logically sound conclusions. VeriMind builds upon these concepts by assigning explicit, distinct roles (Critic, Judge) to separate LLM calls, formalized via LangGraph state machines.")
    doc.add_page_break()

    # ── Chapter 3 ──
    add_heading(doc, "Chapter 3: Methodology", level=1)
    
    add_heading(doc, "3.1 Proposed Model Architecture", level=2)
    add_paragraph(doc, "The VeriMind system is divided into three core layers:\n1. Data Processing & Retrieval Layer (TF-IDF/FAISS)\n2. Multi-Agent Orchestration Layer (LangGraph)\n3. Client Presentation Layer (React + SSE)\n\nUpon uploading a document, it is parsed, chunked, and vectorized. When a user asks a question, the pipeline is triggered:")
    
    add_heading(doc, "3.2 Agent Pipeline Stages", level=2)
    add_paragraph(doc, "• Retrieve: Extracts top-K relevant chunks from the document.\n• Generate: The AnswerGenerator agent drafts an initial response.\n• Debate: The DebateAgent cross-references the draft with the context, listing Agreements, Disagreements, and Key Points.\n• Critic: The CriticAgent scores the draft and identifies specific logical flaws or missing information.\n• Judge: The JudgeAgent synthesizes all feedback to rewrite the draft into a highly accurate, Markdown-formatted final answer.\n• Verify: The VerificationAgent performs a final pass to assign a confidence score and extract exact citations.")
    doc.add_page_break()

    # ── Chapter 4 ──
    add_heading(doc, "Chapter 4: Performance Analysis and Evaluation", level=1)
    add_paragraph(doc, "To evaluate the effectiveness of the VeriMind platform, we compared the output of the full multi-agent pipeline against the initial draft generated by the single AnswerGenerator agent.\n\nMetrics Used:\n• Factual Consistency: How accurately the answer reflects the source document.\n• Format Adherence: How well the answer uses headings, bullets, and structured markdown.\n• Confidence Calibration: The accuracy of the model's reported confidence score vs actual correctness.\n\nResults:\nThe multi-agent pipeline (Judge's output) showed a significant reduction in hallucinations. In complex queries where the single-pass generator fabricated details, the Critic agent successfully identified the unsupported claims, and the Judge agent removed them in the final output. The cost of this accuracy is latency: the single-pass model responds in ~3 seconds, while the full pipeline takes ~12 seconds. To mitigate the UX impact of this latency, Server-Sent Events (SSE) were implemented to provide users with real-time feedback as each agent completes its task.")
    doc.add_page_break()

    # ── Chapter 5 ──
    add_heading(doc, "Chapter 5: Conclusions and Future Work", level=1)
    add_paragraph(doc, "This paper proposed a robust model for document intelligence using a Multi-Agent architecture. The objective of this research was to develop a system that overcomes the hallucination and reasoning limitations of standard RAG models. From the analysis, it was deduced that breaking the cognitive load into specialized agent personas (Generate, Debate, Critic, Judge, Verify) significantly improves output reliability and structure.\n\nFuture Work:\nDespite the good performance demonstrated, the system could be improved by integrating hybrid search (combining dense vector embeddings with BM25 keyword search) for better retrieval recall. Furthermore, the model can be expanded to support web-search fallbacks for queries where the uploaded document lacks sufficient information. Deployment optimizations, such as using smaller, fine-tuned local models for the Critic and Debate nodes, could also greatly reduce the pipeline latency while maintaining high accuracy.")
    
    doc.save(os.path.join("d:\\ASD GenAi Internship\\verimind", "VeriMind_Project_Report.docx"))
    print("Report generated successfully.")

if __name__ == "__main__":
    create_report()
