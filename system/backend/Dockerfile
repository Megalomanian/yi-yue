FROM maven:3.9.9-eclipse-temurin-21 AS build
WORKDIR /build
COPY pom.xml ./
COPY src ./src
RUN mvn -B -ntp -DskipTests package
FROM eclipse-temurin:21-jre-alpine
RUN addgroup -S hub && adduser -S hub -G hub
WORKDIR /app
COPY --from=build /build/target/instrumenthub-1.0.0.jar app.jar
RUN mkdir data && chown -R hub:hub /app
USER hub
EXPOSE 8080
ENTRYPOINT ["java","-Xms128m","-Xmx768m","-jar","app.jar"]
