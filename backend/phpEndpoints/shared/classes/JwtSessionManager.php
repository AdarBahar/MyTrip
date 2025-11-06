<?php
/**
 * JWT Session Manager
 * 
 * Manages JWT-based session tokens for live streaming connections.
 * Provides secure, short-lived tokens with user and device-level access control.
 * 
 * @version 1.0
 * @author Adar Bahar
 */

class JwtSessionManager {
    private $pdo;
    private $secretKey;
    private $defaultDuration;
    private $maxSessionsPerUser;
    
    /**
     * Constructor
     *
     * @param PDO $pdo Database connection
     * @param string $secretKey Secret key for JWT signing (from env)
     * @param int $defaultDuration Default session duration in seconds (default: 3600)
     * @param int $maxSessionsPerUser Maximum active sessions per user (default: 5)
     * @throws Exception if JWT_SECRET_KEY is not configured
     */
    public function __construct($pdo, $secretKey = null, $defaultDuration = 3600, $maxSessionsPerUser = 5) {
        $this->pdo = $pdo;

        // Get secret key from parameter or environment
        $this->secretKey = $secretKey ?? ($_ENV['JWT_SECRET_KEY'] ?? getenv('JWT_SECRET_KEY'));

        // SECURITY: Fail fast if no secret key is configured
        if (!$this->secretKey || $this->secretKey === 'default-secret-key-change-in-production') {
            throw new Exception('JWT_SECRET_KEY must be configured in environment variables. Set JWT_SECRET_KEY in .env or server configuration.');
        }

        $this->defaultDuration = $defaultDuration;
        $this->maxSessionsPerUser = $maxSessionsPerUser;
    }
    
    /**
     * Create a new streaming session
     * 
     * @param int $userId User ID
     * @param array $deviceIds Array of device IDs to stream (empty = all devices)
     * @param int $duration Session duration in seconds (optional)
     * @return array Session data with token
     */
    public function createSession($userId, $deviceIds = [], $duration = null) {
        $duration = $duration ?? $this->defaultDuration;
        
        // Clean up expired sessions first
        $this->cleanupExpiredSessions();
        
        // Check session limit
        $activeCount = $this->getActiveSessionCount($userId);
        if ($activeCount >= $this->maxSessionsPerUser) {
            // Revoke oldest session
            $this->revokeOldestSession($userId);
        }
        
        // Generate session ID
        $sessionId = $this->generateSessionId();
        
        // Create JWT payload
        $issuedAt = time();
        $expiresAt = $issuedAt + $duration;
        
        $payload = [
            'sub' => $userId,
            'device_ids' => $deviceIds,
            'exp' => $expiresAt,
            'iat' => $issuedAt,
            'jti' => $sessionId
        ];
        
        // Generate JWT token
        $token = $this->encodeJwt($payload);
        $tokenHash = hash('sha256', $token);
        
        // Store session in database
        try {
            $stmt = $this->pdo->prepare("
                INSERT INTO streaming_session_tokens (
                    session_id, user_id, device_ids, token_hash,
                    issued_at, expires_at
                ) VALUES (
                    :session_id, :user_id, :device_ids, :token_hash,
                    FROM_UNIXTIME(:issued_at), FROM_UNIXTIME(:expires_at)
                )
            ");
            
            $stmt->execute([
                ':session_id' => $sessionId,
                ':user_id' => $userId,
                ':device_ids' => json_encode($deviceIds),
                ':token_hash' => $tokenHash,
                ':issued_at' => $issuedAt,
                ':expires_at' => $expiresAt
            ]);
            
            return [
                'success' => true,
                'session_id' => $sessionId,
                'session_token' => $token,
                'expires_at' => gmdate('Y-m-d\TH:i:s\Z', $expiresAt),
                'duration' => $duration,
                'stream_url' => '/stream-sse.php?token=' . urlencode($token)
            ];
            
        } catch (Exception $e) {
            error_log("Failed to create session: " . $e->getMessage());
            return [
                'success' => false,
                'error' => 'Failed to create session'
            ];
        }
    }
    
    /**
     * Validate a JWT token
     * 
     * @param string $token JWT token
     * @return array|false Session data if valid, false otherwise
     */
    public function validateToken($token) {
        try {
            // Decode JWT
            $payload = $this->decodeJwt($token);
            
            if (!$payload) {
                return false;
            }
            
            // Check expiration
            if (isset($payload['exp']) && $payload['exp'] < time()) {
                error_log("Token expired: " . $payload['jti']);
                return false;
            }
            
            // Verify token exists in database and is not revoked
            $tokenHash = hash('sha256', $token);
            
            $stmt = $this->pdo->prepare("
                SELECT session_id, user_id, device_ids, expires_at, revoked
                FROM streaming_session_tokens
                WHERE token_hash = :token_hash
                AND expires_at > NOW()
            ");
            
            $stmt->execute([':token_hash' => $tokenHash]);
            $session = $stmt->fetch(PDO::FETCH_ASSOC);
            
            if (!$session || $session['revoked']) {
                return false;
            }
            
            // Parse device_ids JSON
            $deviceIds = json_decode($session['device_ids'], true) ?? [];
            
            return [
                'session_id' => $session['session_id'],
                'user_id' => (int)$session['user_id'],
                'device_ids' => $deviceIds,
                'expires_at' => $session['expires_at']
            ];
            
        } catch (Exception $e) {
            error_log("Token validation failed: " . $e->getMessage());
            return false;
        }
    }
    
    /**
     * Revoke a session
     * 
     * @param string $sessionId Session ID
     * @param int $userId User ID (for authorization)
     * @return bool Success
     */
    public function revokeSession($sessionId, $userId) {
        try {
            $stmt = $this->pdo->prepare("
                UPDATE streaming_session_tokens
                SET revoked = TRUE
                WHERE session_id = :session_id
                AND user_id = :user_id
            ");
            
            $stmt->execute([
                ':session_id' => $sessionId,
                ':user_id' => $userId
            ]);
            
            return $stmt->rowCount() > 0;
            
        } catch (Exception $e) {
            error_log("Failed to revoke session: " . $e->getMessage());
            return false;
        }
    }
    
    /**
     * Get active session count for a user
     * 
     * @param int $userId User ID
     * @return int Active session count
     */
    private function getActiveSessionCount($userId) {
        $stmt = $this->pdo->prepare("
            SELECT COUNT(*) as count
            FROM streaming_session_tokens
            WHERE user_id = :user_id
            AND expires_at > NOW()
            AND revoked = FALSE
        ");
        
        $stmt->execute([':user_id' => $userId]);
        $result = $stmt->fetch(PDO::FETCH_ASSOC);
        
        return (int)$result['count'];
    }
    
    /**
     * Revoke oldest session for a user
     * 
     * @param int $userId User ID
     */
    private function revokeOldestSession($userId) {
        try {
            $stmt = $this->pdo->prepare("
                UPDATE streaming_session_tokens
                SET revoked = TRUE
                WHERE user_id = :user_id
                AND expires_at > NOW()
                AND revoked = FALSE
                ORDER BY issued_at ASC
                LIMIT 1
            ");
            
            $stmt->execute([':user_id' => $userId]);
            
        } catch (Exception $e) {
            error_log("Failed to revoke oldest session: " . $e->getMessage());
        }
    }
    
    /**
     * Clean up expired sessions
     */
    public function cleanupExpiredSessions() {
        try {
            $stmt = $this->pdo->prepare("
                DELETE FROM streaming_session_tokens
                WHERE expires_at < DATE_SUB(NOW(), INTERVAL 1 DAY)
            ");
            
            $stmt->execute();
            
        } catch (Exception $e) {
            error_log("Failed to cleanup expired sessions: " . $e->getMessage());
        }
    }
    
    /**
     * Generate a unique session ID
     * 
     * @return string Session ID
     */
    private function generateSessionId() {
        return 'sess_' . bin2hex(random_bytes(16));
    }
    
    /**
     * Encode JWT token (simple implementation)
     * 
     * @param array $payload Payload data
     * @return string JWT token
     */
    private function encodeJwt($payload) {
        $header = [
            'typ' => 'JWT',
            'alg' => 'HS256'
        ];
        
        $headerEncoded = $this->base64UrlEncode(json_encode($header));
        $payloadEncoded = $this->base64UrlEncode(json_encode($payload));
        
        $signature = hash_hmac('sha256', "$headerEncoded.$payloadEncoded", $this->secretKey, true);
        $signatureEncoded = $this->base64UrlEncode($signature);
        
        return "$headerEncoded.$payloadEncoded.$signatureEncoded";
    }
    
    /**
     * Decode JWT token (simple implementation)
     * 
     * @param string $token JWT token
     * @return array|false Payload if valid, false otherwise
     */
    private function decodeJwt($token) {
        $parts = explode('.', $token);
        
        if (count($parts) !== 3) {
            return false;
        }
        
        list($headerEncoded, $payloadEncoded, $signatureEncoded) = $parts;
        
        // Verify signature
        $signature = hash_hmac('sha256', "$headerEncoded.$payloadEncoded", $this->secretKey, true);
        $signatureCheck = $this->base64UrlEncode($signature);
        
        if ($signatureEncoded !== $signatureCheck) {
            error_log("JWT signature verification failed");
            return false;
        }
        
        // Decode payload
        $payload = json_decode($this->base64UrlDecode($payloadEncoded), true);
        
        return $payload;
    }
    
    /**
     * Base64 URL encode
     * 
     * @param string $data Data to encode
     * @return string Encoded data
     */
    private function base64UrlEncode($data) {
        return rtrim(strtr(base64_encode($data), '+/', '-_'), '=');
    }
    
    /**
     * Base64 URL decode
     * 
     * @param string $data Data to decode
     * @return string Decoded data
     */
    private function base64UrlDecode($data) {
        return base64_decode(strtr($data, '-_', '+/'));
    }
}

