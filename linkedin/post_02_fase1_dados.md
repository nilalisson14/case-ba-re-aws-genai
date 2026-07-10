Segundo dia do projeto de IA na AWS. Hoje foi a camada de dados.

✅ Bucket S3 criado, com criptografia padrão e acesso público bloqueado
✅ Tags de custo (projeto, módulo) desde o primeiro recurso, não depois
✅ Corpus de documentos institucionais sintéticos: pareceres técnicos, manual de procedimentos, nota técnica
✅ Uma divergência proposital entre duas versões do mesmo parecer, para testar depois se a IA pega a inconsistência ou passa reto

Esse último ponto é o que mais me interessa no projeto. Em RAG (Retrieval-Augmented Generation) para ambiente regulado, o risco não é a IA "inventar" informação do nada. É ela responder com segurança usando a versão errada de um documento que já foi corrigido. Por isso desenhei um parecer original, uma revisão que muda um prazo, e uma nota técnica que amarra as duas. Se o sistema não conseguir reconstruir essa linha do tempo, o problema não é de modelo, é de requisito mal levantado.

Próximo passo: liberar os modelos no Bedrock e montar a Knowledge Base que vai transformar esses documentos em respostas com citação de fonte.

#AWS #Bedrock #GenAI #RAG #RequirementsEngineering #BusinessAnalysis #CloudArchitecture
