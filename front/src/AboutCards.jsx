import React from 'react';
import { Box, Grid, useTheme } from "@mui/material";
import { ProfileCardItem } from './ProfileCardItem'; 
import Thiago from './assets/Thiago.jpg'
import Joao from './assets/Joao.jpg'
import Alexandre from './assets/Alexandre.jpg'

// Dados para os 3 cards
const teamMembers = [
    {
        id: 1,
        name: 'Alexandre Evangelista',
        role: 'Front-end Developer',
        desc: 'Profissional em formação em Engenharia da Computação, com experiência em desenvolvimento web, prototipagem e projetos com ESP32 e sistemas preditivos. Possui habilidades em JavaScript, Python, Angular, React, MySQL, Docker e Git, além de design de interfaces, criação de layouts e edição de vídeos. Conta com inglês fluente.',
        image: Alexandre, 
        linkedin: 'https://www.linkedin.com/in/alexandre-e-souza/'
    },
    {
        id: 2,
        name: 'João Guilherme',
        role: 'Back-end Developer',
        desc: 'O idealizador do PrePol, atuando como gerente de proposta e desenvolvedor majoritário, com formação em Engenharia da Computação em andamento, experiência em inteligência artificial, aprendizado de máquina e análise de dados, além de atuação comprovada em projetos de inovação e produção científica.',
        image: Joao, 
        linkedin: 'https://www.linkedin.com/in/jo%C3%A3o-valadares-arcoverde/'
    },
    {
        id: 3,
        name: 'Thiago Paulo',
        role: 'Database Manager',
        desc: 'Profissional em formação em Engenharia da Computação, atuando como estagiário na RNP, com experiência em tecnologia e atividades voltadas ao ambiente acadêmico e científico. Possui vivência prática em redes, sistemas e serviços, além de experiência com desenvolvimento web, prototipagem e metodologias ágeis. Conta com inglês avançado.',
        image: Thiago, 
        linkedin: 'https://www.linkedin.com/in/thiago-paulo-ferreira-da-silva-5499461a7/'
    }
];

export default function AboutCards() {
    const theme = useTheme();
    
    // Cor de fundo do body/page (opcional, se não estiver definido globalmente)
    const pageBackgroundColor = '#0a0a0a'; 

    return (
        <Box
            sx={{
                p: 4,
                width: '100%',
                minHeight: '100vh',
                backgroundColor: pageBackgroundColor, 
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center', // Centraliza verticalmente na tela
            }}
        >
            {/* O Grid Container para organizar os cards */}
            <Grid 
                container 
                spacing={4} // Espaçamento entre os cards (4 unidades MUI)
                justifyContent="center"
                alignItems="stretch" // Essencial para todos os cards terem a mesma altura
                maxWidth="lg" // Limita a largura máxima do conjunto de cards
            >
                {teamMembers.map(member => (
                    // O Grid Item define a responsividade:
                    <Grid 
                        item 
                        key={member.id} 
                        xs={12}    // Largura total (12 colunas) em telas pequenas (empilhados)
                        sm={6}     // Metade da largura (2 por linha) em telas médias
                        md={4}     // Um terço da largura (3 por linha) em telas grandes
                        sx={{ display: 'flex', justifyContent: 'center' }} 
                    >
                        {/* Renderiza o Card de Perfil com os dados da pessoa */}
                        <ProfileCardItem
                            name={member.name}
                            role={member.role}
                            desc={member.desc}
                            image={member.image}
                            linkedinUrl={member.linkedin}
                        />
                    </Grid>
                ))}
            </Grid>
        </Box>
    );
}