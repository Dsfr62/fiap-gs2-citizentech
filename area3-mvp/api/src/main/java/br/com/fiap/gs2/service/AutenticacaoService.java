package br.com.fiap.gs2.service;

import br.com.fiap.gs2.dto.Dtos.CadastroRequest;
import br.com.fiap.gs2.model.Papel;
import br.com.fiap.gs2.model.Usuario;
import br.com.fiap.gs2.repository.UsuarioRepository;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.Locale;

@Service
public class AutenticacaoService implements UserDetailsService {

    private final UsuarioRepository usuarios;
    private final PasswordEncoder passwordEncoder;

    public AutenticacaoService(UsuarioRepository usuarios, PasswordEncoder passwordEncoder) {
        this.usuarios = usuarios;
        this.passwordEncoder = passwordEncoder;
    }

    @Override
    public UserDetails loadUserByUsername(String email) {
        return usuarios.findByEmail(email.toLowerCase(Locale.ROOT))
                .orElseThrow(() -> new UsernameNotFoundException("usuario não encontrado"));
    }

    /** Cadastro aberto cria sempre PRODUTOR: ninguem vira TECNICO sozinho. */
    public Usuario cadastrar(CadastroRequest pedido) {
        String email = pedido.email().trim().toLowerCase(Locale.ROOT);
        if (usuarios.existsByEmail(email)) {
            throw new Erros.Conflito("já existe uma conta com esse e-mail");
        }
        return usuarios.save(new Usuario(pedido.nome().trim(), email,
                passwordEncoder.encode(pedido.senha()), Papel.PRODUTOR));
    }
}
