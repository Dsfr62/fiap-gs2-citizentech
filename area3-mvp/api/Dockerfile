# Imagem da API do Sereno, em duas etapas (Area 4).
# Etapa 1 compila com o JDK; a etapa 2 leva so o JRE e o .jar, sem codigo-fonte nem Maven.

# ---------- etapa 1: build ----------
FROM eclipse-temurin:17-jdk AS build
WORKDIR /build

# Primeiro so o que define as dependencias: enquanto o pom.xml nao muda, o Docker reaproveita esta camada.
COPY .mvn/ .mvn/
COPY mvnw pom.xml ./
RUN chmod +x mvnw && ./mvnw -B -q dependency:go-offline

COPY src/ src/
# Os testes rodam no CI antes desta etapa (job "api"); aqui so empacota.
RUN ./mvnw -B -q package -DskipTests

# ---------- etapa 2: imagem final ----------
FROM eclipse-temurin:17-jre
WORKDIR /app

# Seguranca: a API nao roda como root dentro do conteiner.
RUN useradd --system --uid 1001 --create-home sereno
COPY --from=build /build/target/gs2-api.jar app.jar
USER sereno

EXPOSE 8080
# Limite de memoria pequeno: a API cabe em 256 MB.
ENV JAVA_TOOL_OPTIONS="-Xmx256m"
ENTRYPOINT ["java", "-jar", "/app/app.jar"]
