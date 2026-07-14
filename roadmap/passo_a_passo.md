# Passo a passo: ambiente AWS para o case GenAI de análise documental

Objetivo: transformar o Projeto 3 (estudo de caso) em implementação demonstrável, com evidências para o portfólio e repositório GitHub. Orçamento alvo: menos de US$ 5 no total.

**Status atual (14/07/2026):** Fases 0, 1, 2, 3 e 4 concluídas. Em andamento: Fase 5 (avaliação de qualidade com RAGAS).

## Fase 0 — Conta e proteção de custo ✅ CONCLUÍDA

1. ✅ Conta AWS criada (Free Tier).
2. ✅ MFA ativado no usuário root.
3. ✅ Usuário IAM administrativo criado (`nil-admin`), root reservado para tarefas essenciais.
4. ✅ Budgets configurados: alerta em US$ 5 e alerta em US$ 10.
5. ✅ Região de trabalho definida: **us-east-1 (N. Virginia)**. Achado de requisito confirmado: disponibilidade de modelos Bedrock em sa-east-1 é limitada, validando o RNF de residência de dados como restrição real do case.

Evidência gerada: post no LinkedIn documentando a fundação do projeto (conta, MFA, IAM).

## Fase 1 — Armazenamento e documentos ✅ CONCLUÍDA

1. ✅ Bucket S3 criado: `nil-case-genai-docs`, região us-east-1.
2. ✅ Criptografia padrão (SSE-S3) e acesso público bloqueado.
3. ✅ Corpus de 6 PDFs sintéticos gerados e enviados (decisão: fictícios em vez de documentos reais da ANVISA, para ter gabarito conhecido e controlar divergências propositais):
   - `ANVF-MP-001` — Manual de Procedimentos (regra de prazos por classe de risco)
   - `ANVF-PT-2026-001` — Parecer original (produto DX-7, validade 24 meses)
   - `ANVF-PT-2026-001-R1` — Revisão do mesmo produto (validade retificada para 18 meses) — divergência proposital para testar a HU-03
   - `ANVF-PT-2026-002` — Parecer produto Classe I
   - `ANVF-PT-2026-003` — Parecer produto Classe III
   - `ANVF-NT-2026-010` — Nota técnica que referencia a retificação do R1
4. ✅ Tags aplicadas: `projeto=case-genai`, `modulo=ingestao`.

Evidência gerada: prints do bucket com tags, upload 100% bem-sucedido (6 arquivos, 0 falhas), post no LinkedIn sobre a camada de dados.

## Fase 2 — Bedrock e base de conhecimento RAG (1 a 2 h) ✅ CONCLUÍDA

### 2.1 Solicitar acesso aos modelos ✅ CONCLUÍDO

1. Confirme a região no canto superior direito: **us-east-1 (N. Virginia)**.
2. Busque "Bedrock" na barra de busca do console.
3. Menu lateral esquerdo → **Model catalog**.
4. Filtre por **Providers: Amazon**.
5. Confirmado disponível, sem necessidade de solicitação:
   - **Titan Text Embeddings V2** — Model ID: `amazon.titan-embed-text-v2:0`
   - **Nova 2 Lite** (US) — modelo de geração usado nos testes (versão mais recente disponível no console, substituiu Nova Lite 1.0)

Evidência gerada: prints das páginas de overview dos dois modelos com "Open in playground" habilitado.

### 2.2 Criar a Knowledge Base ✅ CONCLUÍDO

- KB criada: `nil-case-genai-kb` (ID: BWUY1OTUI2), tipo "Knowledge Base with vector store"
- Embeddings: Titan Text Embeddings V2, 1024 dimensões
- Vector store: Amazon S3 Vectors (quick create)
- Data source: S3, bucket `nil-case-genai-docs`, parsing padrão, chunking padrão
- Nota: primeira tentativa de nome da data source falhou por caractere inválido (espaço no final); corrigido para `nil-case-genai-s3-source`

Evidência gerada: print da tela de revisão pré-criação e da KB com status Available.

### 2.3 Sincronizar a base de dados ✅ CONCLUÍDO

- Sync completo em poucos minutos, status "Sync completed for data source"
- 6 documentos processados

Evidência gerada: print com "Sync completed" e Last sync time preenchido.

### 2.4 Testar no console ✅ CONCLUÍDO — resultado acima do esperado

Modelo usado: Nova 2 Lite (US). Modo: Standard retrieval with answer generation.

**Pergunta 1** — "Qual o prazo de validade de registro do Dispositivo de Monitoramento Ambiental Modelo DX-7?"
→ Resposta correta: 18 meses, com reconstrução completa da linha do tempo (parecer original 24 meses → revisão por auditoria de qualidade → 18 meses). Citação com score 0.76, chunk-fonte do documento R1 conferido.

**Pergunta 2** — "Existe alguma retificação de prazo de validade registrada para algum produto?"
→ Resposta correta, puxou a Nota Técnica ANVF-NT-2026-010 como fonte principal. Scores mais baixos (0.44-0.45) que a pergunta 1 — achado registrado para a Fase 5: perguntas genéricas recuperam com menos precisão que perguntas com entidade nomeada.

**Pergunta 3** — "Qual o prazo de validade padrão para produtos de Classe III?"
→ Resposta correta: 12 meses, citando o Manual (ANVF-MP-001) e cruzando com o parecer do RD-9 como exemplo de aplicação consistente (HU-03 na prática). Resposta veio em português (as duas anteriores vieram em inglês) — modelo espelhou o idioma da pergunta sem instrução explícita; observação a registrar na Fase 5 sobre padronização de idioma em produção regulada.

Evidência gerada: 3 prints com respostas e chunks-fonte expandidos (Details). Materializa integralmente a HU-02 e parcialmente a HU-03 e HU-04.

## Fase 3 — API mínima (2 a 3 h) ✅ CONCLUÍDA

> **Nota de direcionamento de carreira (13/07/2026):** decidido manter esta fase como API REST simples (Lambda + Function URL), sem exposição via protocolo MCP neste case. MCP, Bedrock Agents e guardrails ficam reservados para um Projeto 2 dedicado a agentes — ver seção "Escopo final deste case" e "Projeto 2" ao final deste documento. Isso permite fechar este case mais rápido, com um argumento coeso (RAG + Engenharia de Requisitos), em vez de acumular fases avançadas que atrasariam a conclusão.

### O que foi feito

- Role IAM `nil-case-genai-lambda-role` criada (AWS service → Lambda), com policies `AmazonBedrockFullAccess` e `AWSLambdaBasicExecutionRole` anexadas
- Função Lambda `nil-case-genai-query` (Python 3.12), handler `lambda_function.handler`, timeout 30s
- Variáveis de ambiente: `KNOWLEDGE_BASE_ID=BWUY1OTUI2`, `MODEL_ARN=arn:aws:bedrock:us-east-1:539562792209:inference-profile/us.amazon.nova-2-lite-v1:0`
- Function URL criada, Auth type `NONE` (ressalva de segurança documentada: em produção real exigiria autenticação)
- Testado via `curl` no CloudShell: resposta correta (18 meses, citando o documento retificado), contrato JSON completo (`answer`, `citations[]`, `citations_count`, `model_version`)

### Problemas encontrados e corrigidos durante a implementação

1. **Nome da role duplicado na primeira tentativa** (`nil-case-genai-lambda-rolenil-case-genai-lambda-role`) — campo não foi limpo antes de digitar. Corrigido recriando a role.
2. **HTTP 403 / AccessDeniedException** ao chamar a Function URL — causa raiz: a role não tinha a policy `AWSLambdaBasicExecutionRole`, então a Lambda não conseguia nem escrever logs no CloudWatch, e a execução falhava antes de chegar ao código. Corrigido anexando a policy.
3. **Erro de leitura de URL** — um caractere da Function URL foi confundido entre a letra "O" maiúscula e o número "0" ao copiar de um print. Resolvido obtendo a URL exata via `aws lambda get-function-url-config` no CloudShell, em vez de digitar a partir de uma imagem.
4. **Citações duplicadas na primeira versão do código** — a API RetrieveAndGenerate do Bedrock retorna uma citação por segmento de resposta gerado, então a mesma fonte aparecia repetida (8 citações brutas para uma resposta que usava só 4 trechos distintos). Corrigido com deduplicação por chave (documento + trecho), preservando trechos diferentes de um mesmo documento como citações distintas.

### Evidência

Resposta real da API (JSON completo) documentada na Seção 5 do README do repositório. Resultado: `citations_count: 4`, resposta correta citando o documento retificado (R1) e a nota técnica.

1. Criar função Lambda (Python 3.12) que recebe uma pergunta e chama a API RetrieveAndGenerate da Knowledge Base.
2. Retornar JSON com answer, citations[] e model_version, espelhando o contrato de API do case.
3. Expor via Lambda Function URL (mais simples e barato que API Gateway para demo).
4. Testar com curl e guardar request/response de exemplo.

Evidência: trecho do JSON de resposta no README, lado a lado com o contrato especificado no case. É o argumento mais forte do portfólio: especificação e implementação batendo.

## Nota de escopo — Bedrock Agent (12/07/2026)

Avaliamos incorporar um Bedrock Agent (orquestração multi-step, action groups) a este case, inspirado em um diagrama de referência assistido no YouTube. Decisão: **não incorporar aqui**. Motivos:

- Troca a arquitetura de pipeline fixo (RetrieveAndGenerate) por orquestração não determinística — exige reescrever a Lambda principal, criar Lambdas de ferramenta com schema OpenAPI, e revalidar tudo, já que a mesma pergunta pode gerar sequências de passos diferentes em execuções diferentes
- Estimativa: 2-3 dias de trabalho focado, o que atrasaria o fechamento das Fases 4 e 5 já planejadas
- Um case fechado (0 a 5, depois 8) vale mais como portfólio do que um case permanentemente "em evolução"

Agente com Bedrock Agents fica registrado como **Projeto 2, separado**, explorando orquestração multi-step e action groups — degrau acima deste case, que prova RAG + Engenharia de Requisitos. Diagramas de referência (atual e com agente) documentados em `diagrams/arquitetura_atual.mermaid` e `diagrams/arquitetura_com_agente.mermaid` para retomar quando o Projeto 2 começar.

## Fase 4 — Trilha de auditoria estruturada (1 h) ✅ CONCLUÍDA

**Ponto de partida:** a Lambda já loga um evento estruturado por consulta (`logger.info` com `event`, `question`, `citations_count`, `elapsed_ms`, `model_arn`), criado na Fase 3. Isso já vai para o CloudWatch Logs por padrão, no log group `/aws/lambda/nil-case-genai-query`. A Fase 4 formaliza isso para atender a HU-04 por completo, que pede também **usuário** e **fontes citadas** (não só a contagem).

### O que foi feito

1. **Campo de usuário adicionado.** Como não há autenticação real na Function URL (Auth type NONE), o código aceita um campo opcional `user_id` no corpo da requisição, com fallback para `"anonimo"`. Limitação documentada: em produção real, isso viria de um token de autenticação.
2. **Lista completa de documentos citados no log**, não só a contagem — campo `documentos_citados`, com os URIs S3 de cada fonte distinta usada na resposta.
3. **Timestamp explícito em ISO 8601** (`datetime.now(timezone.utc).isoformat()`), independente do timestamp que o CloudWatch já atribui automaticamente a cada linha — facilita consulta via Logs Insights.
4. **Retenção do log group configurada para 30 dias** (era "Never expire" por padrão, o que gera custo crescente sem necessidade para um case).
5. **CloudTrail confirmado** como registrando chamadas ao Bedrock nativamente (não exigiu configuração).

### Evidência real

Consulta de teste (`user_id: "nil.teste"`, pergunta sobre prazo de validade Classe III) gerou o seguinte evento estruturado no CloudWatch Logs:

```json
{
  "event": "consulta_realizada",
  "timestamp": "2026-07-14T00:39:19.271155+00:00",
  "user_id": "nil.teste",
  "question": "Qual o prazo de validade padrão para produtos de Classe III?",
  "citations_count": 2,
  "documentos_citados": [
    "s3://nil-case-genai-docs/ANVF-MP-001_Manual_Procedimentos.pdf",
    "s3://nil-case-genai-docs/ANVF-PT-2026-003_Parecer.pdf"
  ],
  "elapsed_ms": 1945,
  "model_arn": "arn:aws:bedrock:us-east-1:539562792209:inference-profile/us.amazon.nova-2-lite-v1:0"
}
```

Achado registrado: a consulta levou 1945 ms (quase 2 segundos) de ponta a ponta. Dado real de latência a discutir na Fase 5, se a avaliação de qualidade também tocar em performance.

## Fase 5 — Avaliação de qualidade (2 h, diferencial forte) ⬜ PENDENTE

1. Montar conjunto de 10 a 15 perguntas com respostas esperadas baseadas nos PDFs.
2. Rodar RAGAS localmente (Python) contra a API, medindo faithfulness e answer relevancy.
3. Registrar resultados em tabela no README. Conecta diretamente sua experiência de avaliação de LLMs na Turing ao contexto AWS.

## Fase 6 — Empacotar para o portfólio (2 h) ⬜ PENDENTE

1. Repositório GitHub: case-ba-re-aws-genai com README contendo o estudo de caso (Projeto 3), diagrama de arquitetura (draw.io ou Mermaid), prints das evidências, código da Lambda e resultados RAGAS.
2. Atualizar o Projeto 3 no portfólio: trocar "estudo de caso demonstrativo" por "estudo de caso demonstrativo com implementação de referência em AWS".
3. Post no LinkedIn apresentando o case, marcando os temas da vaga (GenAI, RAG, Bedrock, governança).

## Fase 7 — Desligar tudo (30 min, crítica) ⬜ PENDENTE

1. Deletar Knowledge Base, índice S3 Vectors, Lambda e Function URL.
2. Esvaziar e deletar o bucket.
3. Conferir Cost Explorer após 24 h para confirmar custo zero residual.
4. As evidências (prints, código, logs exportados) permanecem no GitHub; a infraestrutura não precisa ficar de pé.

## Estimativa de custo

- S3: centavos
- Bedrock embeddings + geração (corpus pequeno, dezenas de consultas): US$ 1 a 3
- S3 Vectors: centavos
- Lambda e CloudWatch: dentro do free tier
- Total esperado: abaixo de US$ 5, com budget de segurança em US$ 10

## Ordem de execução sugerida

Fases 0 a 2 em um dia (já geram evidência de RAG funcionando). Fases 3 a 5 no segundo dia. Fase 6 e 7 no terceiro. Total: cerca de 10 a 12 horas de trabalho distribuídas.

## Escopo final deste case (atualizado em 13/07/2026)

Este case fecha na **Fase 7** (RAG + API + auditoria + avaliação, documentado e desligado). Duas peças mais avançadas foram avaliadas e conscientemente deixadas de fora daqui, para não atrasar o fechamento de um case coeso:

- **Protocolo MCP** (expor a consulta como ferramenta para qualquer cliente compatível)
- **Bedrock Agent** (orquestração multi-step com action groups, ver nota acima)

As duas ficam reservadas para o **Projeto 2**, junto com guardrails — três peças que fazem mais sentido demonstradas juntas, num case novo focado em agentes, do que espalhadas como fases extras de um case que já tem seu argumento completo (RAG + Engenharia de Requisitos). Ver seção "Projeto 2" ao final deste documento.

**Post de LinkedIn sugerido:** narrativa de evolução ("terminei o case de RAG, o próximo já nasce puxando o fio que ficou de fora") — funciona como ponte natural para anunciar o Projeto 2 sem soar como abandono do primeiro.

---

## Projeto 2 (planejado, não iniciado) — Agente Regulatório com Guardrails

Case novo, construído depois deste estar fechado e publicado. Reaproveita o corpus sintético (ANVF) e a Knowledge Base deste projeto como base de conhecimento, mas muda a arquitetura de pipeline fixo para orquestração de agente.

**O que este projeto teria que o atual não tem:**

- **Bedrock Agent**, não mais `RetrieveAndGenerate` direto — o agente decide se busca, se calcula, se busca de novo, antes de responder (ver `diagrams/arquitetura_com_agente.mermaid`, já esboçado)
- **Action groups** (Lambdas de ferramenta): pelo menos duas, ex. calcular vencimento de prazo a partir de data + regra, e comparar dois documentos apontando divergências — a HU-03 deste case, resolvida de verdade em vez de por sorte estrutural da busca semântica
- **Protocolo MCP**: expor o agente como ferramenta consultável por qualquer cliente compatível (Claude Desktop, outros agentes), não só via API REST
- **Guardrails do Bedrock**: politicas explícitas de conteúdo e de tópico, coerente com a regra de negócio central ("a IA sugere e evidencia, o analista decide") — aqui isso vira configuração declarada, não só texto de especificação

**Por que como projeto separado, não fase deste:** o comportamento de agente é não determinístico (mesma pergunta pode gerar sequências de passos diferentes entre execuções), o que muda completamente a forma de validar e documentar. Misturar isso neste case tornaria a Seção 5 (validação funcional) incomparável entre as fases. Um case novo permite desenhar a validação certa desde o início, em vez de encaixar depois.

**Vagas que motivaram essa direção:** analisadas durante este projeto vagas de AI Engineer pedindo explicitamente "agentes usando protocolo MCP e Python" (Sankhya RH) e "engenharia de IA sênior com agentes, RAG, orquestração" (banco BV) — este segundo projeto mira diretamente esse perfil, enquanto o Projeto 1 (este) prova a base de Requisitos + RAG que sustenta a transição.
