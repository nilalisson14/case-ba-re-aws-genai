# Projeto 3 — Estudo de Caso: Requisitos para Plataforma GenAI de Análise Documental em AWS

**Natureza:** Estudo de caso demonstrativo (não vinculado a cliente). Cenário construído sobre experiência real em Engenharia de Requisitos em ambientes regulados (ANVISA, Petrobras, SEFAZ-PB) e sobre stack GenAI aplicada na prática (RAG, avaliação de LLMs, orquestração).

**Papel:** Analista de Requisitos / Engenheiro de Requisitos

**Domínio:** GenAI aplicada a análise documental em órgão regulado

**Entrega:** Documento de visão, histórias de usuário com critérios BDD, requisitos não funcionais mapeados a serviços AWS, contrato de API e matriz de riscos/conformidade

## Contexto e objetivo

Órgãos reguladores processam grandes volumes de documentos técnicos (petições, laudos, pareceres) com análise manual demorada e inconsistente entre analistas. O estudo de caso especifica os requisitos de uma plataforma de apoio à análise documental com GenAI (arquitetura RAG), hospedada em AWS, que sugere classificações, extrai campos estruturados e aponta inconsistências entre documentos — mantendo o analista humano como decisor final.

O objetivo do artefato é demonstrar como a Engenharia de Requisitos se aplica a um projeto cloud/GenAI: da descoberta com stakeholders à especificação testável, incluindo requisitos não funcionais que orientam decisões de arquitetura AWS.

## Discovery e mapeamento de processo

- Mapeamento AS-IS do fluxo de análise documental: protocolo, triagem, distribuição, análise técnica, parecer — com identificação dos gargalos (triagem manual, retrabalho por inconsistência entre versões de documento).

- Definição do TO-BE com pontos de intervenção da IA claramente delimitados: a IA **sugere e evidencia**, o analista **decide**. Regra de negócio central: nenhuma decisão regulatória é automatizada.

- Identificação de stakeholders e restrições institucionais: LGPD, trilha de auditoria obrigatória, residência de dados em território nacional (região sa-east-1).

## Requisitos funcionais (amostra de histórias de usuário)

**HU-01 — Ingestão de documentos**
Como analista, quero enviar documentos (PDF, DOCX) para a plataforma, para que sejam indexados e fiquem disponíveis para consulta semântica.
- Dado um PDF pesquisável de até 50 MB, quando enviado, então o documento é armazenado, indexado e recebe status "Disponível" em até 5 minutos.
- Dado um PDF digitalizado sem camada de texto, quando enviado, então passa por OCR antes da indexação e o resultado registra o nível de confiança da extração.

**HU-02 — Consulta semântica com evidência**
Como analista, quero perguntar em linguagem natural sobre o conteúdo dos documentos, para localizar informações sem leitura integral.
- Dada uma pergunta, quando respondida, então cada afirmação exibe citação com documento, página e trecho de origem.
- Dado que não há evidência suficiente na base, quando consultado, então o sistema declara a ausência de evidência em vez de gerar resposta especulativa.

**HU-03 — Verificação de consistência entre documentos**
Como analista, quero comparar declarações entre documentos de um mesmo processo, para identificar divergências antes do parecer.
- Dados dois documentos com valores divergentes para o mesmo campo, quando executada a verificação, então a divergência é listada com os dois trechos lado a lado.

**HU-04 — Trilha de auditoria**
Como gestor de conformidade, quero registro imutável de todas as interações com a IA, para atender auditorias internas e externas.
- Dada qualquer consulta ou sugestão da IA, quando gerada, então são registrados usuário, timestamp, prompt, resposta, fontes citadas e versão do modelo.

## Requisitos não funcionais e decisões de arquitetura AWS

| RNF | Especificação | Serviço AWS associado |
|---|---|---|
| Residência de dados | Todo dado em repouso e em processamento na região sa-east-1 | S3, OpenSearch Serverless, Bedrock (verificação de disponibilidade regional como restrição de projeto) |
| Segurança | Criptografia em repouso e em trânsito; segregação por perfil de acesso | KMS, IAM, S3 SSE |
| Auditabilidade | Logs imutáveis de todas as interações, retenção de 5 anos | CloudTrail, CloudWatch Logs, S3 Object Lock |
| Escalabilidade | Ingestão em lote de até 10 mil documentos sem degradação da consulta | Lambda, SQS (fila de ingestão desacoplada) |
| Qualidade da IA | Avaliação contínua de fidelidade e relevância das respostas | Pipeline de avaliação com RAGAS sobre amostras registradas |
| Custo | Estimativa e monitoramento por componente desde o discovery | Cost Explorer, tagging obrigatório por módulo |

Nota metodológica: o mapeamento RNF→serviço demonstra o papel do BA em traduzir restrições de negócio em critérios verificáveis que orientam a arquitetura — a decisão final de arquitetura permanece com o time de engenharia.

## Contrato de API (amostra)

`POST /v1/documents` — ingestão de documento com metadados do processo (número, tipo documental, sigilo). Retorna `document_id` e status de indexação.

`POST /v1/queries` — consulta semântica com escopo por processo. Resposta inclui `answer`, array `citations[]` (documento, página, trecho) e `confidence`.

`GET /v1/audit/interactions` — consulta à trilha de auditoria com filtros por usuário, período e processo. Acesso restrito ao perfil de conformidade.

## Riscos e conformidade

- **Alucinação em contexto regulatório:** mitigado por resposta condicionada a evidência (HU-02), citação obrigatória e avaliação contínua com RAGAS.
- **Vazamento de dados sensíveis:** mitigado por segregação de acesso por processo, mascaramento de dados pessoais na indexação e KMS.
- **Dependência de disponibilidade regional de modelos:** tratado como restrição de projeto verificada no discovery técnico, com alternativa documentada (modelo hospedado em SageMaker na região).
- **Viés de automação (analista aceitar sugestões sem crítica):** mitigado por design — a interface exibe evidências antes da sugestão e exige justificativa registrada para pareceres.

## Competências demonstradas

Discovery com stakeholders em ambiente regulado · Histórias de usuário com critérios BDD testáveis · Especificação de RNFs vinculados a decisões de arquitetura cloud · Definição de contratos de API · Análise de riscos de GenAI (alucinação, auditabilidade, LGPD) · Avaliação de qualidade de LLM (RAGAS, SxS)
