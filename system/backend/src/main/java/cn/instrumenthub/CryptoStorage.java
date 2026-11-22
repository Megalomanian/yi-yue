package cn.instrumenthub;

import io.minio.*;
import java.io.*;
import java.nio.file.*;
import java.security.*;
import java.util.*;
import javax.crypto.Cipher;
import javax.crypto.spec.*;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Component;

@Component
public class CryptoStorage {
  private final byte[] key;
  private final MinioClient minio;
  private final String bucket;
  private final Path localRoot;

  public CryptoStorage(
      @Value("${app.encryption-key}") String secret,
      @Value("${app.storage}") String storage,
      @Value("${app.minio-endpoint}") String endpoint,
      @Value("${app.minio-user}") String user,
      @Value("${app.minio-password}") String password,
      @Value("${app.minio-bucket}") String bucket,
      @Value("${app.local-storage-path:data/reports}") String localRoot)
      throws Exception {
    key =
        MessageDigest.getInstance("SHA-256")
            .digest(secret.getBytes(java.nio.charset.StandardCharsets.UTF_8));
    this.bucket = bucket;
    this.localRoot = Path.of(localRoot);
    minio =
        "minio".equals(storage)
            ? MinioClient.builder().endpoint(endpoint).credentials(user, password).build()
            : null;
  }

  public byte[] encrypt(byte[] input) throws Exception {
    byte[] iv = new byte[12];
    new SecureRandom().nextBytes(iv);
    Cipher c = Cipher.getInstance("AES/GCM/NoPadding");
    c.init(Cipher.ENCRYPT_MODE, new SecretKeySpec(key, "AES"), new GCMParameterSpec(128, iv));
    var out = new ByteArrayOutputStream();
    out.write(iv);
    out.write(c.doFinal(input));
    return out.toByteArray();
  }

  public byte[] decrypt(byte[] input) throws Exception {
    Cipher c = Cipher.getInstance("AES/GCM/NoPadding");
    c.init(
        Cipher.DECRYPT_MODE,
        new SecretKeySpec(key, "AES"),
        new GCMParameterSpec(128, Arrays.copyOf(input, 12)));
    return c.doFinal(Arrays.copyOfRange(input, 12, input.length));
  }

  public String seal(String text) {
    try {
      return Base64.getEncoder()
          .encodeToString(encrypt(text.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
    } catch (Exception e) {
      throw new IllegalStateException(e);
    }
  }

  public String open(String text) {
    try {
      return new String(
          decrypt(Base64.getDecoder().decode(text)), java.nio.charset.StandardCharsets.UTF_8);
    } catch (Exception e) {
      throw new IllegalStateException(e);
    }
  }

  public String put(byte[] input) throws Exception {
    String object = UUID.randomUUID() + ".enc";
    byte[] encrypted = encrypt(input);
    if (minio == null) {
      Files.createDirectories(localRoot);
      Files.write(localRoot.resolve(object), encrypted);
    } else {
      if (!minio.bucketExists(BucketExistsArgs.builder().bucket(bucket).build()))
        minio.makeBucket(MakeBucketArgs.builder().bucket(bucket).build());
      minio.putObject(
          PutObjectArgs.builder().bucket(bucket).object(object).stream(
                  new ByteArrayInputStream(encrypted), encrypted.length, -1)
              .build());
    }
    return object;
  }

  public byte[] read(String object) throws Exception {
    if (minio == null) return decrypt(Files.readAllBytes(localRoot.resolve(object)));
    try (var in = minio.getObject(GetObjectArgs.builder().bucket(bucket).object(object).build())) {
      return decrypt(in.readAllBytes());
    }
  }
}
