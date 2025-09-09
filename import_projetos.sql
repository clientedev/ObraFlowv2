-- Importação dos 105 projetos em lote
-- Script gerado automaticamente para PostgreSQL

INSERT INTO projetos (
    numero, nome, endereco, status, tipo_obra, 
    responsavel_id, construtora, nome_funcionario, email_principal,
    latitude, longitude, data_criacao, data_atualizacao
) VALUES
-- 1. Ápice Aclimação
(1, 'Ápice Aclimação', 'Rua Gama Cerqueira 577 - Cambuci', 'Ativo', 'Residencial', 1, 'Construtora Filippo', 'Eng. Marcelo Izar', 'marcelo@filippo.com.br', -23.550520, -46.633308, NOW(), NOW()),

-- 2-6. Astral Saúde (5 registros)
(2, 'Astral Saúde', 'R. Carneiro da Cunha 555 - Vila da Saúde', 'Concluído', 'Residencial', 1, 'Tecnisa', 'Eng. Bruna Cristina da Silva Souza', 'bruna.souza@tecnisa.com.br', -23.550520, -46.633308, NOW(), NOW()),
(3, 'Astral Saúde', 'R. Carneiro da Cunha 555 - Vila da Saúde', 'Concluído', 'Residencial', 1, 'Tecnisa', 'Eng. Rosa Alice Sant anna', 'eng.rosa@tecnisa.com.br', -23.550520, -46.633308, NOW(), NOW()),
(4, 'Astral Saúde', 'R. Carneiro da Cunha 555 - Vila da Saúde', 'Concluído', 'Residencial', 1, 'Tecnisa', 'Gustavo Bomfim Carvalho de Almeida', 'gustavo.almeida@tecnisa.com.br', -23.550520, -46.633308, NOW(), NOW()),
(5, 'Astral Saúde', 'R. Carneiro da Cunha 555 - Vila da Saúde', 'Concluído', 'Residencial', 1, 'Tecnisa', 'Eng. Luana Sato', 'luana.sato@tecnisa.com.br', -23.550520, -46.633308, NOW(), NOW()),
(6, 'Astral Saúde', 'R. Carneiro da Cunha 555 - Vila da Saúde', 'Concluído', 'Residencial', 1, 'Tecnisa', 'Bruno Andrelini De Freitas', 'bruno.andrelini@tecnisa.com.br', -23.550520, -46.633308, NOW(), NOW()),

-- 7-8. Baume (2 registros)
(7, 'Baume', 'R. Consórcio 130 - Vila Nova Conceição', 'Ativo', 'Residencial', 1, 'OR', 'Felipe Nogueira Brunelli', 'felipebrunelli@or.com.br', -23.550520, -46.633308, NOW(), NOW()),
(8, 'Baume', 'R. Consórcio 130 - Vila Nova Conceição', 'Ativo', 'Residencial', 1, 'OR', 'Diego Moreira Campos', 'diegomcampos@or.com.br', -23.550520, -46.633308, NOW(), NOW()),

-- 9-12. Biotique Ibirapuera (4 registros)
(9, 'Biotique Ibirapuera', 'R. Manuel da Nóbrega 778 - Paraíso', 'Ativo', 'Residencial', 1, 'Porto Ferraz', 'Luana Assis', 'luana.assis@portoferraz.com.br', -23.550520, -46.633308, NOW(), NOW()),
(10, 'Biotique Ibirapuera', 'R. Manuel da Nóbrega 778 - Paraíso', 'Ativo', 'Residencial', 1, 'Porto Ferraz', 'Carlos Marques', 'carlos.marques@portoferraz.com.br', -23.550520, -46.633308, NOW(), NOW()),
(11, 'Biotique Ibirapuera', 'R. Manuel da Nóbrega 778 - Paraíso', 'Ativo', 'Residencial', 1, 'Porto Ferraz', 'Bruna Costa', 'bruna.costa@portoferraz.com.br', -23.550520, -46.633308, NOW(), NOW()),
(12, 'Biotique Ibirapuera', 'R. Manuel da Nóbrega 778 - Paraíso', 'Ativo', 'Residencial', 1, 'Porto Ferraz', 'Caio Brito', 'caio.brito@portoferraz.com.br', -23.550520, -46.633308, NOW(), NOW()),

-- 13-17. Bosque das Pitangueiras (5 registros)
(13, 'Bosque das Pitangueiras', 'Rua Arnaldo Jose Pacifico 18', 'Ativo', 'Residencial', 1, 'Tecnisa', 'Vitor Teixeira Carneiro da Cunha', 'vitor.cunha@tecnisa.com.br', -23.550520, -46.633308, NOW(), NOW()),
(14, 'Bosque das Pitangueiras', 'Rua Arnaldo Jose Pacifico 18', 'Ativo', 'Residencial', 1, 'Tecnisa', 'Giovanna Teixeira Custodio', 'giovanna.custodio@tecnisa.com.br', -23.550520, -46.633308, NOW(), NOW()),
(15, 'Bosque das Pitangueiras', 'Rua Arnaldo Jose Pacifico 18', 'Ativo', 'Residencial', 1, 'Tecnisa', 'Daniel Bonini Pereira', 'daniel.pereira@tecnisa.com.br', -23.550520, -46.633308, NOW(), NOW()),
(16, 'Bosque das Pitangueiras', 'Rua Arnaldo Jose Pacifico 18', 'Ativo', 'Residencial', 1, 'Tecnisa', 'Fabio Yuzo Yoda', 'fabio.yoda@tecnisa.com.br', -23.550520, -46.633308, NOW(), NOW()),
(17, 'Bosque das Pitangueiras', 'Rua Arnaldo Jose Pacifico 18', 'Ativo', 'Residencial', 1, 'Tecnisa', 'Eng. Luana Sato', 'luana.sato@tecnisa.com.br', -23.550520, -46.633308, NOW(), NOW()),

-- 18-23. Casa Alto de Pinheiros (6 registros)
(18, 'Casa Alto de Pinheiros', 'Av. Diógenes Ribeiro de Lima 2440', 'Concluído', 'Residencial', 1, 'Even Construtora', 'Wesley Soares Fernandes Nobre', 'wfernandes@even.com.br', -23.550520, -46.633308, NOW(), NOW()),
(19, 'Casa Alto de Pinheiros', 'Av. Diógenes Ribeiro de Lima 2441', 'Concluído', 'Residencial', 1, 'Even Construtora', 'Isabella Soriani Almeida', 'isalmeida@even.com.br', -23.550520, -46.633308, NOW(), NOW()),
(20, 'Casa Alto de Pinheiros', 'Av. Diógenes Ribeiro de Lima 2442', 'Concluído', 'Residencial', 1, 'Even Construtora', 'Vinicius Alves Bassi', 'vabassi@even.com.br', -23.550520, -46.633308, NOW(), NOW()),
(21, 'Casa Alto de Pinheiros', 'Av. Diógenes Ribeiro de Lima 2443', 'Concluído', 'Residencial', 1, 'Even Construtora', 'Maria Luisa Figueiredo', 'mafigueiredo@even.com.br', -23.550520, -46.633308, NOW(), NOW()),
(22, 'Casa Alto de Pinheiros', 'Av. Diógenes Ribeiro de Lima 2444', 'Concluído', 'Residencial', 1, 'Even Construtora', 'Rodrigo Augusto Estrada Carvalho Do Nascimento', 'ranascimento@even.com.br', -23.550520, -46.633308, NOW(), NOW()),
(23, 'Casa Alto de Pinheiros', 'Av. Diógenes Ribeiro de Lima 2445', 'Concluído', 'Residencial', 1, 'Even Construtora', 'Anderson Machado', 'amachado@even.com.br', -23.550520, -46.633308, NOW(), NOW()),

-- 24-28. Casa Jardim Ibirapuera (5 registros)
(24, 'Casa Jardim Ibirapuera', 'Av. Piassanguaba 326 - Planalto Paulista', 'Ativo', 'Residencial', 1, 'MV Construção', 'Diogo', 'estagioeng.ibirapuera@mvconstrucoes.com.br', -23.550520, -46.633308, NOW(), NOW()),
(25, 'Casa Jardim Ibirapuera', 'Av. Piassanguaba 326 - Planalto Paulista', 'Ativo', 'Residencial', 1, 'MV Construção', 'Victor Coutinho', 'victor.coutinho@mvconstrucoes.com.br', -23.550520, -46.633308, NOW(), NOW()),
(26, 'Casa Jardim Ibirapuera', 'Av. Piassanguaba 326 - Planalto Paulista', 'Ativo', 'Residencial', 1, 'MV Construção', 'Alexandre Zafiro', 'alexandre.zafiro@mvconstrucoes.com.br', -23.550520, -46.633308, NOW(), NOW()),
(27, 'Casa Jardim Ibirapuera', 'Av. Piassanguaba 326 - Planalto Paulista', 'Ativo', 'Residencial', 1, 'MV Construção', 'Adriana Siqueira', 'adriana.siqueira@mvconstrucoes.com.br', -23.550520, -46.633308, NOW(), NOW()),
(28, 'Casa Jardim Ibirapuera', 'Av. Piassanguaba 326 - Planalto Paulista', 'Ativo', 'Residencial', 1, 'MV Construção', 'Kayque Sousa', 'kayque.sousa@mvconstrucoes.com.br', -23.550520, -46.633308, NOW(), NOW()),

-- 29-32. Casa Jardim Kansas (4 registros)
(29, 'Casa Jardim Kansas', 'Rua Kansas 101, Brooklin, São Paulo', 'Ativo', 'Residencial', 1, 'MV Construção', 'Adriana Siqueira', 'adriana.siqueira@mvconstrucoes.com.br', -23.550520, -46.633308, NOW(), NOW()),
(30, 'Casa Jardim Kansas', 'Rua Kansas 101, Brooklin, São Paulo', 'Ativo', 'Residencial', 1, 'MV Construção', 'Kayque Sousa', 'kayque.sousa@mvconstrucoes.com.br', -23.550520, -46.633308, NOW(), NOW()),
(31, 'Casa Jardim Kansas', 'Rua Kansas 101, Brooklin, São Paulo', 'Ativo', 'Residencial', 1, 'MV Construção', 'Douglas Castro', 'douglas.castro@mvconstrucoes.com.br', -23.550520, -46.633308, NOW(), NOW()),
(32, 'Casa Jardim Kansas', 'Rua Kansas 101, Brooklin, São Paulo', 'Ativo', 'Residencial', 1, 'MV Construção', 'Lucas Aires', 'lucas.aires@mvconstrucoes.com.br', -23.550520, -46.633308, NOW(), NOW()),

-- 33-36. Casa Jardim Laplace (4 registros)
(33, 'Casa Jardim Laplace', 'R. Laplace 352', 'Ativo', 'Residencial', 1, 'MV Construção', 'Adriana Siqueira', 'adriana.siqueira@mvconstrucoes.com.br', -23.550520, -46.633308, NOW(), NOW()),
(34, 'Casa Jardim Laplace', 'R. Laplace 352', 'Ativo', 'Residencial', 1, 'MV Construção', 'Kayque Sousa', 'kayque.sousa@mvconstrucoes.com.br', -23.550520, -46.633308, NOW(), NOW()),
(35, 'Casa Jardim Laplace', 'R. Laplace 352', 'Ativo', 'Residencial', 1, 'MV Construção', 'Joselia Andrade', 'joselia.andrade@mvconstrucoes.com.br', -23.550520, -46.633308, NOW(), NOW()),
(36, 'Casa Jardim Laplace', 'R. Laplace 352', 'Ativo', 'Residencial', 1, 'MV Construção', 'Vinicius Oliveira', 'vinicius.oliveira@mvconstrucoes.com.br', -23.550520, -46.633308, NOW(), NOW()),

-- 37-39. Casa Magnólia (3 registros)
(37, 'Casa Magnólia', 'Avenida das Magnólias 679', 'Ativo', 'Residencial', 1, 'R. Yazbek', 'Cintia Santos', 'cintia.santos@ryazbek.com.br', -23.550520, -46.633308, NOW(), NOW()),
(38, 'Casa Magnólia', 'Avenida das Magnólias 679', 'Ativo', 'Residencial', 1, 'R. Yazbek', 'Mirella Cavalcante', 'mirella@ryazbek.com.br', -23.550520, -46.633308, NOW(), NOW()),
(39, 'Casa Magnólia', 'Avenida das Magnólias 679', 'Ativo', 'Residencial', 1, 'R. Yazbek', 'Henry Camargo', 'henry.camargo@ryazbek.com.br', -23.550520, -46.633308, NOW(), NOW()),

-- 40-41. Cond. Duquesa de São Francisco (2 registros)
(40, 'Cond. Duquesa de São Francisco', 'Alameda Sibipuruna, 167 - Jd. Adalgisa - Osasco - SP', 'Ativo', 'Residencial', 1, 'Condomínio', 'Reginaldo Corrêa - Sindico', 'contato@sttrategia.com', -23.550520, -46.633308, NOW(), NOW()),
(41, 'Cond. Duquesa de São Francisco', 'Alameda Sibipuruna, 167 - Jd. Adalgisa - Osasco - SP', 'Ativo', 'Residencial', 1, 'Condomínio', 'Administração', 'gerencia.duquesa@gmail.com', -23.550520, -46.633308, NOW(), NOW()),

-- 42. Esther Ibirapuera
(42, 'Esther Ibirapuera', 'R. Manuel da Nóbrega 950', 'Ativo', 'Residencial', 1, 'Even Construtora', 'Engenharia', 'nf.esther@even.com.br', -23.550520, -46.633308, NOW(), NOW()),

-- 43-44. Greenview Brooklyn (2 registros)
(43, 'Greenview Brooklyn', 'R. São Sebastião 318', 'Ativo', 'Residencial', 1, 'Patrimônio', 'Cauane Ribeiro', 'cauane.ribeiro@patrimoniodi.com.br', -23.550520, -46.633308, NOW(), NOW()),
(44, 'Greenview Brooklyn', 'R. São Sebastião 318', 'Ativo', 'Residencial', 1, 'Patrimônio', 'Iago Alves Faria', 'iago.faria@patrimoniodi.com.br', -23.550520, -46.633308, NOW(), NOW()),

-- 45. Joaquim
(45, 'Joaquim', 'Rua R. Joaquim Guarani 322 - Brooklin - São Paulo', 'Concluído', 'Residencial', 1, 'Even Construtora', 'Engenharia', 'nf.joaquim@even.com.br', -23.550520, -46.633308, NOW(), NOW()),

-- 46-49. Kalea Jardins (4 registros)
(46, 'Kalea Jardins', 'Rua da Consolação 3288', 'Ativo', 'Residencial', 1, 'Tecnisa', 'Marcela Murgia', 'marcela.murgia@tecnisa.com.br', -23.550520, -46.633308, NOW(), NOW()),
(47, 'Kalea Jardins', 'Rua da Consolação 3289', 'Ativo', 'Residencial', 1, 'Tecnisa', 'Adailson Cardoso Teixeira', 'adailson.teixeira@tecnisa.com.br', -23.550520, -46.633308, NOW(), NOW()),
(48, 'Kalea Jardins', 'Rua da Consolação 3290', 'Ativo', 'Residencial', 1, 'Tecnisa', 'Renato Pimentel Gomes', 'renato.gomes@tecnisa.com.br', -23.550520, -46.633308, NOW(), NOW()),
(49, 'Kalea Jardins', 'Rua da Consolação 3291', 'Ativo', 'Residencial', 1, 'Tecnisa', 'Eng. Luana Sato', 'luana.sato@tecnisa.com.br', -23.550520, -46.633308, NOW(), NOW()),

-- 50. Madre de Deus
(50, 'Madre de Deus', 'Rua Madre de Deus, 503', 'Ativo', 'Residencial', 1, 'Even Construtora', 'Engenharia', 'madre@even.com.br', -23.550520, -46.633308, NOW(), NOW()),

-- 51-54. Mirant Ibirapuera (4 registros)
(51, 'Mirant Ibirapuera', 'Rua Pedro de Toledo 388', 'Ativo', 'Residencial', 1, 'Trisul', 'Gabriel Xavier', 'gabrielxavier@trisul.com.br', -23.550520, -46.633308, NOW(), NOW()),
(52, 'Mirant Ibirapuera', 'Rua Pedro de Toledo 388', 'Ativo', 'Residencial', 1, 'Trisul', 'Bismarck Albuquerque', 'bismarckalbuquerque@trisul.com.br', -23.550520, -46.633308, NOW(), NOW()),
(53, 'Mirant Ibirapuera', 'Rua Pedro de Toledo 388', 'Ativo', 'Residencial', 1, 'Trisul', 'Isabella Silva', 'isabellasilva@trisul.com.br', -23.550520, -46.633308, NOW(), NOW()),
(54, 'Mirant Ibirapuera', 'Rua Pedro de Toledo 388', 'Ativo', 'Residencial', 1, 'Trisul', 'Aline Collacite', 'alinecollacite@trisul.com.br', -23.550520, -46.633308, NOW(), NOW()),

-- 55-58. MOD Paulista (4 registros)
(55, 'MOD Paulista', 'Rua Maestro Cardim - 1143 - Bela Vista - São Paulo', 'Ativo', 'Residencial', 1, 'Niss / GNG', 'Bruna Garcia', 'bruna.garcia@gng.com.br', -23.550520, -46.633308, NOW(), NOW()),
(56, 'MOD Paulista', 'Rua Maestro Cardim - 1143 - Bela Vista - São Paulo', 'Ativo', 'Residencial', 1, 'Niss / GNG', 'José Carlos', 'jose.carlos@gng.com.br', -23.550520, -46.633308, NOW(), NOW()),
(57, 'MOD Paulista', 'Rua Maestro Cardim - 1143 - Bela Vista - São Paulo', 'Ativo', 'Residencial', 1, 'Niss / GNG', 'Thaís Oliveira', 'thais.oliveira@gng.com.br', -23.550520, -46.633308, NOW(), NOW()),
(58, 'MOD Paulista', 'Rua Maestro Cardim - 1143 - Bela Vista - São Paulo', 'Ativo', 'Residencial', 1, 'Niss / GNG', 'Jéssica Paixão', 'jessica.paixao@niss.com.br', -23.550520, -46.633308, NOW(), NOW()),

-- 59-65. Monã (7 registros)
(59, 'Monã', 'Av Indianópolis 618', 'Ativo', 'Residencial', 1, 'Diálogo Engenharia', 'Wialan Santos', 'wialan.santos@dialogo.com.br', -23.550520, -46.633308, NOW(), NOW()),
(60, 'Monã', 'Av Indianópolis 618', 'Ativo', 'Residencial', 1, 'Diálogo Engenharia', 'Rafael Bellis', 'rafael.bellis@dialogo.com.br', -23.550520, -46.633308, NOW(), NOW()),
(61, 'Monã', 'Av Indianópolis 618', 'Ativo', 'Residencial', 1, 'Diálogo Engenharia', 'Thiago Ribeiro', 'thiago.ribeiro@dialogo.com.br', -23.550520, -46.633308, NOW(), NOW()),
(62, 'Monã', 'Av Indianópolis 618', 'Ativo', 'Residencial', 1, 'Diálogo Engenharia', 'Marcelo Soares', 'marcelo.soares@dialogo.com.br', -23.550520, -46.633308, NOW(), NOW()),
(63, 'Monã', 'Av Indianópolis 618', 'Ativo', 'Residencial', 1, 'Diálogo Engenharia', 'Luanderson Melo', 'luanderson.melo@dialogo.com.br', -23.550520, -46.633308, NOW(), NOW()),
(64, 'Monã', 'Av Indianópolis 618', 'Ativo', 'Residencial', 1, 'Diálogo Engenharia', 'Andres Herran', 'andres.herran@dialogo.com.br', -23.550520, -46.633308, NOW(), NOW()),
(65, 'Monã', 'Av Indianópolis 618', 'Ativo', 'Residencial', 1, 'Diálogo Engenharia', 'Breno Cury', 'breno.cury@dialogo.com.br', -23.550520, -46.633308, NOW(), NOW()),

-- 66-69. PJM 319 (4 registros)
(66, 'PJM 319', 'R. Padre João Manuel 319 - Cerqueira César', 'Ativo', 'Residencial', 1, 'Trisul', 'Arthur Sileo', 'arthursileo@trisul.com.br', -23.550520, -46.633308, NOW(), NOW()),
(67, 'PJM 319', 'R. Padre João Manuel 319 - Cerqueira César', 'Ativo', 'Residencial', 1, 'Trisul', 'Stephany Carassoli', 'stephanycarassoli@trisul.com.br', -23.550520, -46.633308, NOW(), NOW()),
(68, 'PJM 319', 'R. Padre João Manuel 319 - Cerqueira César', 'Ativo', 'Residencial', 1, 'Trisul', 'Maria Camila', 'mariasilva@trisul.com.br', -23.550520, -46.633308, NOW(), NOW()),
(69, 'PJM 319', 'R. Padre João Manuel 319 - Cerqueira César', 'Ativo', 'Residencial', 1, 'Trisul', 'Ariane Esteves', 'arianeesteves@trisul.com.br', -23.550520, -46.633308, NOW(), NOW()),

-- 70-72. Praça dos Omaguás (3 registros)
(70, 'Praça dos Omaguás', 'R. Inácio Pereira da Rocha 597 - Pinheiros - São Paulo', 'Ativo', 'Residencial', 1, 'Trisul', 'Danilo Scarpitta', 'daniloscarpitta@trisul.com.br', -23.550520, -46.633308, NOW(), NOW()),
(71, 'Praça dos Omaguás', 'R. Inácio Pereira da Rocha 597 - Pinheiros - São Paulo', 'Ativo', 'Residencial', 1, 'Trisul', 'Stephany Carassoli', 'stephanycarassoli@trisul.com.br', -23.550520, -46.633308, NOW(), NOW()),
(72, 'Praça dos Omaguás', 'R. Inácio Pereira da Rocha 597 - Pinheiros - São Paulo', 'Ativo', 'Residencial', 1, 'Trisul', 'Luan Silva', 'luansilva@trisul.com.br', -23.550520, -46.633308, NOW(), NOW()),

-- 73-78. Prado Paulista (6 registros)
(73, 'Prado Paulista', 'R. Pamplona 112 - Bela Vista', 'Ativo', 'Residencial', 1, 'Porto Ferraz', 'Lucas Oliveira', 'lucas.oliveira@portoferraz.com.br', -23.550520, -46.633308, NOW(), NOW()),
(74, 'Prado Paulista', 'R. Pamplona 112 - Bela Vista', 'Ativo', 'Residencial', 1, 'Porto Ferraz', 'Carlos Marques', 'carlos.marques@portoferraz.com.br', -23.550520, -46.633308, NOW(), NOW()),
(75, 'Prado Paulista', 'R. Pamplona 112 - Bela Vista', 'Ativo', 'Residencial', 1, 'Porto Ferraz', 'Mateus Lima', 'mateus.lima@portoferraz.com.br', -23.550520, -46.633308, NOW(), NOW()),
(76, 'Prado Paulista', 'R. Pamplona 112 - Bela Vista', 'Ativo', 'Residencial', 1, 'Porto Ferraz', 'Guilherme Rezende', 'guilherme.rezende@portoferraz.com.br', -23.550520, -46.633308, NOW(), NOW()),
(77, 'Prado Paulista', 'R. Pamplona 112 - Bela Vista', 'Ativo', 'Residencial', 1, 'Porto Ferraz', 'Bruno Paraventi', 'bruno.paraventi@portoferraz.com.br', -23.550520, -46.633308, NOW(), NOW()),
(78, 'Prado Paulista', 'R. Pamplona 112 - Bela Vista', 'Ativo', 'Residencial', 1, 'Porto Ferraz', 'Thais Flor', 'thais.flor@portoferraz.com.br', -23.550520, -46.633308, NOW(), NOW()),

-- 79-82. Reserva das Figueiras (4 registros)
(79, 'Reserva das Figueiras', 'Rua Arnaldo Jose Pacifico 20', 'Ativo', 'Residencial', 1, 'Tecnisa', 'Fabio Yuzo Yoda', 'fabio.yoda@tecnisa.com.br', -23.550520, -46.633308, NOW(), NOW()),
(80, 'Reserva das Figueiras', 'Rua Arnaldo Jose Pacifico 20', 'Ativo', 'Residencial', 1, 'Tecnisa', 'Eng. Luana Sato', 'luana.sato@tecnisa.com.br', -23.550520, -46.633308, NOW(), NOW()),
(81, 'Reserva das Figueiras', 'Rua Arnaldo Jose Pacifico 20', 'Ativo', 'Residencial', 1, 'Tecnisa', 'Marcos Vinicius Lacerda Soprani', 'marcos.soprani@tecnisa.com.br', -23.550520, -46.633308, NOW(), NOW()),
(82, 'Reserva das Figueiras', 'Rua Arnaldo Jose Pacifico 20', 'Ativo', 'Residencial', 1, 'Tecnisa', 'Vanessa Gomes Ivonica', 'vanessa.ivonica@tecnisa.com.br', -23.550520, -46.633308, NOW(), NOW()),

-- 83-86. Side sacomã (4 registros)
(83, 'Side sacomã', 'Rua do Lago 216', 'Ativo', 'Residencial', 1, 'Trisul', 'André Oliveira', 'andreoliveira@trisul.com.br', -23.550520, -46.633308, NOW(), NOW()),
(84, 'Side sacomã', 'Rua do Lago 216', 'Ativo', 'Residencial', 1, 'Trisul', 'Lucas Ricarte', 'lucasricarte@trisul.com.br', -23.550520, -46.633308, NOW(), NOW()),
(85, 'Side sacomã', 'Rua do Lago 216', 'Ativo', 'Residencial', 1, 'Trisul', 'Vinicius Correia', 'viniciuscorreia@trisul.com.br', -23.550520, -46.633308, NOW(), NOW()),
(86, 'Side sacomã', 'Rua do Lago 216', 'Ativo', 'Residencial', 1, 'Trisul', 'Rafael Silva', 'rafaelsilva@trisul.com.br', -23.550520, -46.633308, NOW(), NOW()),

-- 87-89. TRIU 1722 (3 registros)
(87, 'TRIU 1722', 'Rua Barão de Triunfo 1722', 'Ativo', 'Residencial', 1, 'MSB Sanchez', 'Pedro Sanchez', 'pedro@msbsanchez.com.br', -23.550520, -46.633308, NOW(), NOW()),
(88, 'TRIU 1722', 'Rua Barão de Triunfo 1722', 'Ativo', 'Residencial', 1, 'MSB Sanchez', 'Carolina Iervolino', 'carolina.iervolino@msbsanchez.com.br', -23.550520, -46.633308, NOW(), NOW()),
(89, 'TRIU 1722', 'Rua Barão de Triunfo 1722', 'Ativo', 'Residencial', 1, 'MSB Sanchez', 'Antonio Nour', 'tony@msbsanchez.com.br', -23.550520, -46.633308, NOW(), NOW()),

-- 90-91. Valen (2 registros)
(90, 'Valen', 'Rua Capote Valente 65', 'Ativo', 'Residencial', 1, 'Trisul', 'Wallace Lemos', 'wallacelemos@trisul.com.br', -23.550520, -46.633308, NOW(), NOW()),
(91, 'Valen', 'Rua Capote Valente 65', 'Ativo', 'Residencial', 1, 'Trisul', 'Leonardo Dionísio', 'leonardodionizio@trisul.com.br', -23.550520, -46.633308, NOW(), NOW()),

-- 92-96. Visconde de Guaratiba (5 registros)
(92, 'Visconde de Guaratiba', 'Rua Visconde de Guaratiba 218', 'Ativo', 'Residencial', 1, 'Tecnisa', 'Bruna Matias Maia', 'bruna.maia@tecnisa.com.br', -23.550520, -46.633308, NOW(), NOW()),
(93, 'Visconde de Guaratiba', 'Rua Visconde de Guaratiba 218', 'Ativo', 'Residencial', 1, 'Tecnisa', 'Marcus Vieira', 'Marcus.vieira@tecnisa.com.br', -23.550520, -46.633308, NOW(), NOW()),
(94, 'Visconde de Guaratiba', 'Rua Visconde de Guaratiba 218', 'Ativo', 'Residencial', 1, 'Tecnisa', 'Renata Matsunaga', 'Renata.matsunaga@tecnisa.com.br', -23.550520, -46.633308, NOW(), NOW()),
(95, 'Visconde de Guaratiba', 'Rua Visconde de Guaratiba 218', 'Ativo', 'Residencial', 1, 'Tecnisa', 'Kayo Cyrillo', 'kayo.cyrillo@tecnisa.com.br', -23.550520, -46.633308, NOW(), NOW()),
(96, 'Visconde de Guaratiba', 'Rua Visconde de Guaratiba 218', 'Ativo', 'Residencial', 1, 'Tecnisa', 'Eng. Luana Sato', 'luana.sato@tecnisa.com.br', -23.550520, -46.633308, NOW(), NOW()),

-- 97-101. Vista Park Ibirapuera (5 registros)
(97, 'Vista Park Ibirapuera', 'R. Dra. Neyde Apparecida Sollitto, 252/306 - Vila Clementino', 'Concluído', 'Residencial', 1, 'Construtora RFM', 'Vinicius Vieira', 'vinicius.vieira@rfm.com.br', -23.550520, -46.633308, NOW(), NOW()),
(98, 'Vista Park Ibirapuera', 'R. Dra. Neyde Apparecida Sollitto, 252/306 - Vila Clementino', 'Concluído', 'Residencial', 1, 'Construtora RFM', 'Julio Andrade Olicio Maia', 'julio.maia@rfm.com.br', -23.550520, -46.633308, NOW(), NOW()),
(99, 'Vista Park Ibirapuera', 'R. Dra. Neyde Apparecida Sollitto, 252/306 - Vila Clementino', 'Concluído', 'Residencial', 1, 'Construtora RFM', 'Adryann Matheus Lima Alves', 'adryann.alves@rfm.com.br', -23.550520, -46.633308, NOW(), NOW()),
(100, 'Vista Park Ibirapuera', 'R. Dra. Neyde Apparecida Sollitto, 252/306 - Vila Clementino', 'Concluído', 'Residencial', 1, 'Construtora RFM', 'Gustavo Mendonca Cacau Nascimento', 'gustavo.mendonca@rfm.com.br', -23.550520, -46.633308, NOW(), NOW()),
(101, 'Vista Park Ibirapuera', 'R. Dra. Neyde Apparecida Sollitto, 252/306 - Vila Clementino', 'Concluído', 'Residencial', 1, 'Construtora RFM', 'Bettyandra Cavalcante Machado', 'bettyandra@rfm.com.br', -23.550520, -46.633308, NOW(), NOW()),

-- 102-105. Zeit Brooklin (4 registros)
(102, 'Zeit Brooklin', 'Rua Francisco Dias Velho, 51 - Vila Cordeiro', 'Ativo', 'Residencial', 1, 'Setin / Vero', 'Aline Santos', 'aline.santos@veroincorporadora.com.br', -23.550520, -46.633308, NOW(), NOW()),
(103, 'Zeit Brooklin', 'Rua Francisco Dias Velho, 51 - Vila Cordeiro', 'Ativo', 'Residencial', 1, 'Setin / Vero', 'Erica Juliato', 'erica.juliato@veroincorporadora.com.br', -23.550520, -46.633308, NOW(), NOW()),
(104, 'Zeit Brooklin', 'Rua Francisco Dias Velho, 51 - Vila Cordeiro', 'Ativo', 'Residencial', 1, 'Setin / Vero', 'Priscila Coelho', 'priscila.coelho@veroincorporadora.com.br', -23.550520, -46.633308, NOW(), NOW()),
(105, 'Zeit Brooklin', 'Rua Francisco Dias Velho, 51 - Vila Cordeiro', 'Ativo', 'Residencial', 1, 'Setin / Vero', 'Gustavo Rangel', 'gustavo.rangel@veroincorporadora.com.br', -23.550520, -46.633308, NOW(), NOW());

-- Verificar se a importação foi bem-sucedida
SELECT COUNT(*) as total_projetos_importados FROM projetos;
SELECT numero, nome, status, construtora FROM projetos ORDER BY numero LIMIT 10;