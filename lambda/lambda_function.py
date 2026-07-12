"""
Lambda de orquestração do case GenAI (Fase 3).

Recebe uma pergunta via Function URL (POST /v1/queries), chama a Knowledge Base
do Bedrock (RetrieveAndGenerate) e devolve um JSON no contrato especificado
no caso de uso: answer, citations[], model_version.

Variáveis de ambiente esperadas:
  KNOWLEDGE_BASE_ID  -> ID da Knowledge Base (ex.: BWUY1OTUI2)
  MODEL_ARN          -> ARN completo do modelo de geração (Nova 2 Lite, perfil US)
"""

import json
import os
import logging
import time
import boto3

logger = logging.getLogger()
logger.setLevel(logging.INFO)

bedrock_agent_runtime = boto3.client("bedrock-agent-runtime")

KNOWLEDGE_BASE_ID = os.environ.get("KNOWLEDGE_BASE_ID", "")
MODEL_ARN = os.environ.get("MODEL_ARN", "")


def _cors_headers():
    return {
        "Content-Type": "application/json",
        "Access-Control-Allow-Origin": "*",
    }


def _error_response(status_code, message):
    return {
        "statusCode": status_code,
        "headers": _cors_headers(),
        "body": json.dumps({"error": message}, ensure_ascii=False),
    }


def _extract_citations(citations_raw):
    """
    Achata a estrutura de citações da API do Bedrock para o formato do contrato.

    A API retorna uma citação por segmento da resposta gerada, então a mesma
    fonte costuma aparecer repetida quando vários trechos da resposta se apoiam
    nela. Para o analista, isso é ruído: o que importa é a lista de fontes
    distintas que sustentam a resposta. Deduplicamos por (documento, trecho),
    preservando a ordem de primeira aparição.
    """
    citations = []
    vistos = set()

    for citation in citations_raw:
        refs = citation.get("retrievedReferences", [])
        for ref in refs:
            location = ref.get("location", {})
            s3_location = location.get("s3Location", {})
            content = ref.get("content", {}).get("text", "")

            documento = s3_location.get("uri", "desconhecido")
            trecho = content[:500]  # limite defensivo de tamanho

            chave = (documento, trecho)
            if chave in vistos:
                continue

            vistos.add(chave)
            citations.append({
                "document": documento,
                "excerpt": trecho,
            })

    return citations


def handler(event, context):
    start_time = time.time()

    # A Function URL entrega o corpo como string JSON em event["body"]
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _error_response(400, "Corpo da requisição não é um JSON válido.")

    question = body.get("question", "").strip()
    if not question:
        return _error_response(400, "Campo 'question' é obrigatório.")

    if not KNOWLEDGE_BASE_ID or not MODEL_ARN:
        logger.error("Variáveis de ambiente KNOWLEDGE_BASE_ID ou MODEL_ARN não configuradas.")
        return _error_response(500, "Configuração do servidor incompleta.")

    try:
        response = bedrock_agent_runtime.retrieve_and_generate(
            input={"text": question},
            retrieveAndGenerateConfiguration={
                "type": "KNOWLEDGE_BASE",
                "knowledgeBaseConfiguration": {
                    "knowledgeBaseId": KNOWLEDGE_BASE_ID,
                    "modelArn": MODEL_ARN,
                },
            },
        )
    except Exception as exc:  # captura ampla proposital: qualquer falha do Bedrock vira 502 controlado
        logger.exception("Falha ao chamar RetrieveAndGenerate")
        return _error_response(502, f"Falha ao consultar a base de conhecimento: {str(exc)}")

    answer_text = response.get("output", {}).get("text", "")
    citations_raw = response.get("citations", [])
    citations = _extract_citations(citations_raw)

    elapsed_ms = int((time.time() - start_time) * 1000)

    # Trilha de auditoria mínima (HU-04 parcial) — log estruturado no CloudWatch.
    # A Fase 4 vai formalizar isso com mais campos e um log group dedicado.
    logger.info(json.dumps({
        "event": "consulta_realizada",
        "question": question,
        "citations_count": len(citations),
        "elapsed_ms": elapsed_ms,
        "model_arn": MODEL_ARN,
    }, ensure_ascii=False))

    result = {
        "answer": answer_text,
        "citations": citations,
        "citations_count": len(citations),
        "model_version": MODEL_ARN,
    }

    return {
        "statusCode": 200,
        "headers": _cors_headers(),
        "body": json.dumps(result, ensure_ascii=False),
    }
