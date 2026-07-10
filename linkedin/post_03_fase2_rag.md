Terceiro dia do projeto de IA na AWS. Essa foi a etapa que eu mais queria ver funcionar.

✅ Knowledge Base criada no Amazon Bedrock, usando Titan Text Embeddings V2 e S3 Vectors como índice
✅ Corpus de 6 documentos sincronizado e indexado
✅ Pergunta de teste: qual o prazo de validade do dispositivo DX-7
✅ Resposta: 18 meses, não 24

Eu tinha montado o corpus de propósito com um parecer técnico original (validade de 24 meses) e uma revisão posterior que corrigia esse prazo para 18. A pergunta parece simples, mas testa algo que todo projeto de RAG em ambiente regulado precisa resolver: não basta buscar o documento certo, é preciso buscar a versão certa dele.

O sistema achou o parecer original, achou a nota técnica que explicava a retificação, e respondeu com a informação atualizada, citando o trecho exato de cada afirmação.

Um detalhe que ainda vou olhar com mais calma: perguntas genéricas voltaram com score de relevância mais baixo do que perguntas com o nome do produto. Ainda não sei se isso é ruído do corpus pequeno ou um padrão real, mas é o tipo de coisa que quero medir direito antes de confiar.

Próximo passo: tirar essa consulta do console e transformar em API, com Lambda.

#AWS #Bedrock #RAG #GenAI #RequirementsEngineering #BusinessAnalysis #CloudArchitecture
